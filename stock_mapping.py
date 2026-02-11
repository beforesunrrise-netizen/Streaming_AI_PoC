"""
Stock name to code mapping for common Korean stocks
This is a fallback when Daum Finance search is unavailable
"""

# Common Korean stock mappings
STOCK_MAPPING = {
    # 삼성 그룹
    "삼성전자": "005930",
    "삼성": "005930",  # Default to 삼성전자
    "삼성SDI": "006400",
    "삼성물산": "028260",
    "삼성생명": "032830",
    "삼성화재": "000810",
    "삼성중공업": "010140",
    "삼성엔지니어링": "028050",
    "삼성바이오로직스": "207940",
    "삼성전기": "009150",

    # SK 그룹
    "SK하이닉스": "000660",
    "하이닉스": "000660",
    "SK": "034730",
    "SK이노베이션": "096770",
    "SK텔레콤": "017670",
    "SK케미칼": "285130",
    "SKC": "011790",

    # 현대 그룹
    "현대차": "005380",
    "현대자동차": "005380",
    "현대모비스": "012330",
    "기아": "000270",
    "기아차": "000270",
    "현대중공업": "009540",
    "현대건설": "000720",
    "현대제철": "004020",

    # LG 그룹
    "LG전자": "066570",
    "LG화학": "051910",
    "LG에너지솔루션": "373220",
    "LG": "003550",
    "LG디스플레이": "034220",
    "LG생활건강": "051900",
    "LG유플러스": "032640",

    # 포스코 그룹
    "포스코": "005490",
    "포스코홀딩스": "005490",
    "포스코케미칼": "003670",

    # 네이버/카카오
    "네이버": "035420",
    "NAVER": "035420",
    "카카오": "035720",
    "카카오뱅크": "323410",
    "카카오페이": "377300",
    "카카오게임즈": "293490",

    # 금융
    "KB금융": "105560",
    "신한지주": "055550",
    "하나금융지주": "086790",
    "우리금융": "316140",
    "NH투자증권": "005940",

    # 통신
    "KT": "030200",
    "LG유플러스": "032640",

    # 항공/운송
    "대한항공": "003490",
    "아시아나항공": "020560",

    # 유통
    "롯데쇼핑": "023530",
    "신세계": "004170",
    "현대백화점": "069960",

    # 제약/바이오
    "셀트리온": "068270",
    "삼성바이오로직스": "207940",
    "한미약품": "128940",
    "유한양행": "000100",
    "녹십자": "006280",

    # 엔터테인먼트
    "하이브": "352820",
    "HYBE": "352820",
    "JYP": "035900",
    "SM": "041510",
    "YG": "122870",

    # 기타 주요 기업
    "CJ": "001040",
    "CJ제일제당": "097950",
    "두산": "000150",
    "한화": "000880",
    "GS": "078930",
    "LS": "006260",
}


def get_stock_code(stock_name: str) -> tuple:
    """
    Get stock code from name using mapping

    Args:
        stock_name: Korean stock name

    Returns:
        (code, name) tuple or None
    """
    # Direct match
    if stock_name in STOCK_MAPPING:
        return (STOCK_MAPPING[stock_name], stock_name)

    # Try partial match
    for name, code in STOCK_MAPPING.items():
        if stock_name in name or name in stock_name:
            return (code, name)

    return None


def get_stock_name(stock_code: str) -> str:
    """
    Get stock name from code

    Args:
        stock_code: 6-digit stock code

    Returns:
        Stock name or None
    """
    # Remove A prefix if exists
    clean_code = stock_code.replace('A', '') if stock_code.startswith('A') else stock_code

    for name, code in STOCK_MAPPING.items():
        if code == clean_code:
            return name

    return None
