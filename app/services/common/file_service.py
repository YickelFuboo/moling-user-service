import os
import uuid
import io
import logging
from PIL import Image
from datetime import datetime
from typing import Optional, BinaryIO
from app.config.settings import settings
from app.infrastructure.storage.factory import STORAGE_CONN
from app.constants.common import AVATAR_MAX_SIZE_KB, AVATAR_IMAGE_TYPES


class FileType:
    AVATAR = "avatar"


class FileService:
    """文件服务 - 统一使用 file_id 作为标识符"""
    
    # 文件类型配置
    FILE_TYPE_CONFIG = {
        FileType.AVATAR: {
            "allowed_extensions": AVATAR_IMAGE_TYPES,
            "max_size_kb": AVATAR_MAX_SIZE_KB,
            "bucket": "avatars",
            "content_type_prefix": "image/",
            "process_image": True,
            "max_dimensions": (300, 300)
        }
    }

    @staticmethod
    async def upload_file_by_type(file_data: BinaryIO, filename: str, file_type: FileType, **kwargs) -> Optional[str]:
        """
        根据文件类型上传文件
        
        Args:
            file_data: 文件数据
            filename: 原始文件名
            file_type: 文件类型（FileType枚举）
            **kwargs: 额外参数（如：user_id等）
            
        Returns:
            str: file_id (UUID)
        """
        try:
            # 验证文件类型
            if file_type.value not in FileService.FILE_TYPE_CONFIG:
                logging.error(f"不支持的文件类型: {file_type.value}")
                return None
            
            config = FileService.FILE_TYPE_CONFIG[file_type.value] # 获取文件类型配置
            
            # 验证文件扩展名（如果配置了允许的扩展名）
            if config["allowed_extensions"]:
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext not in config["allowed_extensions"]:
                    raise ValueError(f"不支持的文件类型: {file_ext}")
            
            # 检查文件大小
            file_data.seek(0, 2)  # 移动到文件末尾
            file_size = file_data.tell()
            file_data.seek(0)  # 重置到文件开头
            if config["max_size_kb"] and file_size > config["max_size_kb"] * 1024:
                logging.error(f"文件大小超过限制: {file_size} bytes")
                return None
            
            # 处理图片（如果需要且是图片文件）
            if config["process_image"] and FileService._is_image_file(file_ext):
                file_data = FileService._process_image(file_data, config["max_dimensions"])
            
            # 准备元数据
            metadata = {
                "original_filename": filename,
                "upload_time": datetime.utcnow().isoformat(),
                "file_size": file_size,
                "content_type": f"{config['content_type_prefix']}{file_ext[1:]}"
            }
            
            # 添加额外参数到元数据
            for key, value in kwargs.items():
                metadata[key] = value
            
            # 上传到存储层，返回 file_id
            file_id = await STORAGE_CONN.put(
                file_index=filename,
                file_data=file_data,
                bucket_name=config["bucket"],
                content_type=metadata["content_type"],
                metadata=metadata
            )
            
            logging.info(f"文件上传成功: file_id={file_id}, file_type={file_type}")
            return file_id
            
        except Exception as e:
            logging.error(f"文件上传失败: {e}")
            return None

    @staticmethod
    async def get_file_url(file_id: str, file_type: FileType, expires_in: Optional[int] = None) -> Optional[str]:
        """
        获取文件URL
        
        Args:
            file_id: 文件ID
            file_type: 文件类型（FileType枚举）
            expires_in: URL过期时间（秒）
            
        Returns:
            str: 文件访问URL
        """
        try:
            if file_type.value not in FileService.FILE_TYPE_CONFIG:
                logging.error(f"不支持的文件类型: {file_type.value}")
                return None
                
            config = FileService.FILE_TYPE_CONFIG[file_type.value]
            url = await STORAGE_CONN.get_url(
                file_index=file_id,
                bucket_name=config["bucket"],
                expires_in=expires_in
            )
            return url
        except Exception as e:
            logging.error(f"获取文件URL失败: {e}")
            return None

    @staticmethod
    async def delete_file(file_id: str, file_type: FileType) -> bool:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            file_type: 文件类型（FileType枚举）
            
        Returns:
            bool: 是否删除成功
        """
        try:
            if file_type.value not in FileService.FILE_TYPE_CONFIG:
                logging.error(f"不支持的文件类型: {file_type.value}")
                return False
                
            config = FileService.FILE_TYPE_CONFIG[file_type.value]
            success = await STORAGE_CONN.delete(
                file_index=file_id,
                bucket_name=config["bucket"]
            )
            if success:
                logging.info(f"文件删除成功: file_id={file_id}, file_type={file_type}")
            return success
        except Exception as e:
            logging.error(f"删除文件失败: {e}")
            return False

    @staticmethod
    async def get_file_metadata(file_id: str, file_type: FileType) -> Optional[dict]:
        """
        获取文件元数据
        
        Args:
            file_id: 文件ID
            file_type: 文件类型（FileType枚举）
            
        Returns:
            dict: 文件元数据
        """
        try:
            if file_type.value not in FileService.FILE_TYPE_CONFIG:
                logging.error(f"不支持的文件类型: {file_type.value}")
                return None
                
            config = FileService.FILE_TYPE_CONFIG[file_type.value]
            metadata = await STORAGE_CONN.get_metadata(
                file_index=file_id,
                bucket_name=config["bucket"]
            )
            return metadata
        except Exception as e:
            logging.error(f"获取文件元数据失败: {e}")
            return None

    @staticmethod
    def _is_image_file(file_ext: str) -> bool:
        """判断文件是否为图片类型"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.svg'}
        return file_ext.lower() in image_extensions

    @staticmethod
    def _process_image(file_data: BinaryIO, max_dimensions: tuple) -> BinaryIO:
        """处理图片（调整大小、格式转换等）"""
        try:            
            # 打开图片
            image = Image.open(file_data)
            
            # 调整大小（保持宽高比）
            image.thumbnail(max_dimensions, Image.Resampling.LANCZOS)
            
            # 转换为JPEG格式
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            return output
            
        except Exception as e:
            logging.error(f"图片处理失败: {e}")
            return file_data 