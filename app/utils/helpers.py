"""工具函数。"""

import re
import hashlib
from urllib.parse import urlparse, parse_qs


# BVID 正则: BV + 10位字母数字
BVID_PATTERN = re.compile(r"^BV[a-zA-Z0-9]{10}$")


def is_valid_bvid(s: str) -> bool:
    """校验 BVID 格式。"""
    return bool(BVID_PATTERN.match(s))


def is_valid_cvid(s: str | int) -> bool:
    """校验专栏 CV ID。"""
    try:
        return int(s) > 0
    except (ValueError, TypeError):
        return False


def md5_hex(text: str) -> str:
    """计算 MD5 十六进制摘要。"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def extract_filename_from_url(url: str) -> str:
    """从 URL 中提取文件名。"""
    path = urlparse(url).path
    return path.rsplit("/", 1)[-1] or "unknown"


# ----- BVID/AID 互转（算法参考 B站 官方实现）-----

XOR_CODE = 23442827791579
MAX_AID = 1 << 51
ALPHABET = "FcwAPNKTMug3GV5Lj7EJnHpWsx4tb8haYeviqBz6rkCy12mUSDQX9RdoZf"
ALPHABET_LEN = len(ALPHABET)


def bvid_to_aid(bvid: str) -> int:
    """BV 号转 AV 号。"""
    if not is_valid_bvid(bvid):
        raise ValueError(f"Invalid BVID: {bvid}")
    r = _bvid_decode(bvid)
    return (r - XOR_CODE) ^ MAX_AID


def aid_to_bvid(aid: int) -> str:
    """AV 号转 BV 号。"""
    a = (aid ^ MAX_AID) + XOR_CODE
    return _bvid_encode(a)


def _bvid_decode(bvid: str) -> int:
    """BVID Base58 解码。"""
    result = 0
    for char in bvid[3:]:  # 跳过 "BV1"
        idx = ALPHABET.index(char)
        result = result * ALPHABET_LEN + idx
    return result


def _bvid_encode(num: int) -> str:
    """BVID Base58 编码。"""
    chars = []
    while num > 0:
        num, rem = divmod(num, ALPHABET_LEN)
        chars.append(ALPHABET[rem])
    result = "".join(reversed(chars))
    # 填充到固定长度，以 "BV1" 开头
    return f"BV1{result:0>9s}"[:12]
