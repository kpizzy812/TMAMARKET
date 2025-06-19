"""
Сервис для работы с изображениями товаров
Загрузка, обработка, валидация изображений
"""

import os
import hashlib
import aiofiles
from typing import Optional
from PIL import Image
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.product import Product
from app.schemas.product import ProductUpdateSchema
from app.core.config import marketplace_settings


class ProductImageService:
    """Сервис для работы с изображениями товаров"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_product_image(
        self,
        product_id: int,
        image_data: bytes,
        filename: str,
        optimize: bool = True
    ) -> Optional[str]:
        """
        Сохранение изображения товара

        Args:
            product_id: ID товара
            image_data: Данные изображения
            filename: Имя файла
            optimize: Оптимизировать изображение

        Returns:
            Путь к сохраненному файлу или None
        """
        try:
            # Валидация изображения
            validation_result = await self._validate_image(image_data, filename)
            if not validation_result["valid"]:
                logger.warning(f"⚠️ Невалидное изображение: {validation_result['reason']}")
                return None

            # Создаем директорию если не существует
            upload_dir = os.path.join(marketplace_settings.UPLOAD_PATH, "products")
            os.makedirs(upload_dir, exist_ok=True)

            # Генерируем уникальное имя файла
            file_extension = self._get_file_extension(filename)
            new_filename = await self._generate_filename(product_id, image_data, file_extension)
            file_path = os.path.join(upload_dir, new_filename)

            # Оптимизируем изображение если нужно
            if optimize:
                image_data = await self._optimize_image(image_data)

            # Сохраняем файл
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(image_data)

            # Обновляем путь в базе данных
            relative_path = f"products/{new_filename}"
            await self._update_product_image_path(product_id, relative_path)

            logger.success(f"✅ Сохранено изображение товара {product_id}: {relative_path}")
            return relative_path

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения изображения товара {product_id}: {e}")
            return None

    async def delete_product_image(self, product_id: int) -> bool:
        """
        Удаление изображения товара

        Args:
            product_id: ID товара

        Returns:
            True если удалено успешно
        """
        try:
            # Получаем товар
            product = await self._get_product(product_id)
            if not product or not product.image_path:
                return True  # Нет изображения для удаления

            # Удаляем файл
            file_path = os.path.join(marketplace_settings.UPLOAD_PATH, product.image_path)
            if os.path.exists(file_path):
                os.remove(file_path)

            # Очищаем путь в БД
            await self._update_product_image_path(product_id, None)

            logger.info(f"📦 Удалено изображение товара {product_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка удаления изображения товара {product_id}: {e}")
            return False

    async def get_image_info(self, product_id: int) -> Optional[dict]:
        """
        Получение информации об изображении товара

        Args:
            product_id: ID товара

        Returns:
            Словарь с информацией об изображении
        """
        try:
            product = await self._get_product(product_id)
            if not product:
                return None

            result = {
                "has_image": bool(product.image_path),
                "image_path": product.image_path,
                "image_url": product.image_url
            }

            # Если есть локальный файл, получаем его размер
            if product.image_path:
                file_path = os.path.join(marketplace_settings.UPLOAD_PATH, product.image_path)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    result["file_size"] = file_size

                    # Получаем размеры изображения
                    try:
                        with Image.open(file_path) as img:
                            result["width"] = img.width
                            result["height"] = img.height
                            result["format"] = img.format
                    except Exception:
                        pass

            return result

        except Exception as e:
            logger.error(f"❌ Ошибка получения информации об изображении товара {product_id}: {e}")
            return None

    async def _validate_image(self, image_data: bytes, filename: str) -> dict:
        """
        Валидация изображения

        Args:
            image_data: Данные изображения
            filename: Имя файла

        Returns:
            Словарь с результатом валидации
        """
        try:
            # Проверяем размер файла
            if len(image_data) > marketplace_settings.MAX_FILE_SIZE:
                return {
                    "valid": False,
                    "reason": f"Файл слишком большой. Максимум: {marketplace_settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
                }

            # Проверяем расширение файла
            file_extension = self._get_file_extension(filename).lower()
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            if file_extension not in allowed_extensions:
                return {
                    "valid": False,
                    "reason": f"Неподдерживаемый формат. Разрешены: {', '.join(allowed_extensions)}"
                }

            # Проверяем что это действительно изображение
            try:
                with Image.open(BytesIO(image_data)) as img:
                    # Проверяем размеры изображения
                    if img.width < 100 or img.height < 100:
                        return {
                            "valid": False,
                            "reason": "Изображение слишком маленькое. Минимум: 100x100 пикселей"
                        }

                    if img.width > 4000 or img.height > 4000:
                        return {
                            "valid": False,
                            "reason": "Изображение слишком большое. Максимум: 4000x4000 пикселей"
                        }

            except Exception:
                return {
                    "valid": False,
                    "reason": "Файл не является корректным изображением"
                }

            return {"valid": True, "reason": "Изображение валидно"}

        except Exception as e:
            logger.error(f"❌ Ошибка валидации изображения: {e}")
            return {"valid": False, "reason": "Ошибка валидации"}

    async def _optimize_image(self, image_data: bytes) -> bytes:
        """
        Оптимизация изображения

        Args:
            image_data: Исходные данные изображения

        Returns:
            Оптимизированные данные изображения
        """
        try:
            with Image.open(BytesIO(image_data)) as img:
                # Конвертируем в RGB если нужно
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Создаем белый фон для прозрачных изображений
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background

                # Изменяем размер если слишком большое
                max_size = (1920, 1920)
                if img.width > max_size[0] or img.height > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Сохраняем в оптимизированном формате
                output = BytesIO()
                img.save(
                    output,
                    format='JPEG',
                    quality=85,
                    optimize=True,
                    progressive=True
                )

                return output.getvalue()

        except Exception as e:
            logger.error(f"❌ Ошибка оптимизации изображения: {e}")
            return image_data  # Возвращаем исходные данные если не удалось оптимизировать

    async def _generate_filename(self, product_id: int, image_data: bytes, extension: str) -> str:
        """
        Генерация уникального имени файла

        Args:
            product_id: ID товара
            image_data: Данные изображения
            extension: Расширение файла

        Returns:
            Уникальное имя файла
        """
        # Создаем хеш от данных изображения
        image_hash = hashlib.md5(image_data).hexdigest()[:8]

        # Генерируем имя файла
        filename = f"product_{product_id}_{image_hash}{extension}"

        return filename

    def _get_file_extension(self, filename: str) -> str:
        """Получение расширения файла"""
        return os.path.splitext(filename)[1].lower()

    async def _get_product(self, product_id: int) -> Optional[Product]:
        """Получение товара по ID"""
        try:
            from sqlalchemy import select
            query = select(Product).where(Product.id == product_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Ошибка получения товара {product_id}: {e}")
            return None

    async def _update_product_image_path(self, product_id: int, image_path: Optional[str]) -> bool:
        """
        Обновление пути к изображению в БД

        Args:
            product_id: ID товара
            image_path: Новый путь к изображению

        Returns:
            True если обновлено успешно
        """
        try:
            product = await self._get_product(product_id)
            if not product:
                return False

            product.image_path = image_path
            await self.session.commit()

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка обновления пути изображения товара {product_id}: {e}")
            await self.session.rollback()
            return False