import re
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional

def fuzzy_match(text: str, query: str, threshold: float = 0.6) -> bool:
    """
    퍼지 매칭 함수: 텍스트와 쿼리 간의 유사도 계산
    
    Args:
        text: 대상 텍스트
        query: 검색어
        threshold: 유사도 임계값 (0.0 ~ 1.0)
        
    Returns:
        유사도가 임계값 이상이면 True, 아니면 False
    """
    # 널값 처리
    if text is None or query is None:
        return False
        
    # 정확히 포함된 경우
    if query.lower() in text.lower():
        return True
    
    # 한글 초성 검색 지원
    if is_korean(query) and matches_initial_consonants(text, query):
        return True
    
    # 유사도 계산
    similarity = calculate_similarity(text, query)
    return similarity >= threshold

def calculate_similarity(text: str, query: str) -> float:
    """
    두 문자열 간의 유사도 계산
    
    Args:
        text: 대상 텍스트
        query: 검색어
        
    Returns:
        유사도 (0.0 ~ 1.0)
    """
    # 모두 소문자로 변환하여 비교
    text_lower = text.lower()
    query_lower = query.lower()
    
    # 정확히 포함된 경우 높은 점수 부여
    if query_lower in text_lower:
        return 0.9
    
    # difflib의 SequenceMatcher 사용
    matcher = SequenceMatcher(None, text_lower, query_lower)
    return matcher.ratio()

def is_korean(text: str) -> bool:
    """
    문자열이 한글인지 확인
    
    Args:
        text: 확인할 문자열
        
    Returns:
        한글이 포함되어 있으면 True, 아니면 False
    """
    # 한글 유니코드 범위: AC00-D7A3 (가-힣)
    return bool(re.search(r'[가-힣]', text))

def get_initial_consonant(char: str) -> Optional[str]:
    """
    한글 문자의 초성을 반환
    
    Args:
        char: 한글 문자 (한 글자)
        
    Returns:
        초성 문자 또는 None
    """
    if not is_korean(char):
        return None
    
    # 한글 초성 목록
    CHOSUNG = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    
    # 한글 유니코드 계산
    char_code = ord(char) - 0xAC00
    
    # 초성 인덱스 계산
    idx = char_code // (21 * 28)
    
    # 인덱스가 범위 내인지 확인
    if 0 <= idx < len(CHOSUNG):
        return CHOSUNG[idx]
    
    return None

def extract_initial_consonants(text: str) -> str:
    """
    문자열에서 한글 초성만 추출
    
    Args:
        text: 대상 문자열
        
    Returns:
        초성만 추출한 문자열
    """
    result = ""
    
    for char in text:
        if is_korean(char):
            initial = get_initial_consonant(char)
            if initial:
                result += initial
        else:
            result += char
    
    return result

def matches_initial_consonants(text: str, query: str) -> bool:
    """
    문자열이 주어진 초성 패턴과 일치하는지 확인
    
    Args:
        text: 대상 문자열
        query: 초성 패턴 (ㅅㅇㅎ 등)
        
    Returns:
        초성 패턴이 일치하면 True, 아니면 False
    """
    # 검색어가 모두 한글 초성인지 확인
    if not all(char in 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ' for char in query):
        return False
    
    # 대상 문자열의 초성만 추출
    text_initials = extract_initial_consonants(text)
    
    # 추출한 초성에 검색 패턴이 포함되는지 확인
    return query in text_initials