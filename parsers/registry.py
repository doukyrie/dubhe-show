from core import DataParserFactory
from .image_parser import CommonImageParser, EnviERDASParser
from .video_parser import CommonVideoParser

from .image_parser import GeoTIFFParser
from .pointcloud_parser import LasLazParser, PCDParser, E57Parser
from .scientific_parser import HDF5Parser, NetCDFParser
from .json_parser import JSONParser
from .other_parser import VTKParser, NMEAParser

# 图像类解析器
DataParserFactory.register_parser("CommonImage", CommonImageParser)
DataParserFactory.register_parser("EnviImage/ERDASImage", EnviERDASParser)
DataParserFactory.register_parser("GeoTIFFImage", GeoTIFFParser)

# 视频类解析器
DataParserFactory.register_parser("CommonVideo", CommonVideoParser)

## 点云类数据集
DataParserFactory.register_parser("LAS/LAZ", LasLazParser)
DataParserFactory.register_parser("PCD", PCDParser)
DataParserFactory.register_parser("E57", E57Parser)

## 科学统计类数据集
DataParserFactory.register_parser("NetCDF", NetCDFParser)
DataParserFactory.register_parser("HDF5", HDF5Parser)

# JSON 数据集
DataParserFactory.register_parser("JSON", JSONParser)

# 其他的数据类型
DataParserFactory.register_parser("VTK", VTKParser)
DataParserFactory.register_parser("NMEA", NMEAParser)