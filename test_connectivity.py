"""
Network connectivity test page for debugging
Run with: streamlit run test_connectivity.py
"""

import streamlit as st
import requests
from config import DEFAULT_HEADERS, DEFAULT_TIMEOUT
from daum_fetch import fetch, get_session
import time

st.set_page_config(
    page_title="네트워크 연결 테스트",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 네트워크 연결 테스트")
st.markdown("Streamlit Cloud 환경에서 다음 금융 접속 가능 여부를 확인합니다.")

# Test URLs
test_urls = [
    ("다음 금융 메인", "https://finance.daum.net/"),
    ("검색 - 삼성전자", "https://finance.daum.net/search/search?q=삼성전자"),
    ("시세 - 삼성전자", "https://finance.daum.net/quotes/005930"),
    ("뉴스 - 삼성전자", "https://finance.daum.net/quotes/005930/news"),
]

st.header("📊 연결 테스트 결과")

if st.button("🔄 테스트 시작", type="primary"):
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (name, url) in enumerate(test_urls):
        status_text.text(f"테스트 중: {name}...")
        
        # Test with daum_fetch
        start_time = time.time()
        result = fetch(url, use_cache=False)
        elapsed = time.time() - start_time
        
        results.append({
            "name": name,
            "url": url,
            "success": result.success,
            "status_code": result.status_code,
            "error": result.error_message,
            "elapsed": elapsed
        })
        
        progress_bar.progress((i + 1) / len(test_urls))
    
    status_text.empty()
    progress_bar.empty()
    
    # Display results
    for r in results:
        with st.expander(f"{'✅' if r['success'] else '❌'} {r['name']} ({r['elapsed']:.2f}초)", expanded=not r['success']):
            st.code(f"URL: {r['url']}")
            
            if r['success']:
                st.success(f"성공! HTTP {r['status_code']}")
            else:
                st.error(f"실패: {r['error']}")
                if r['status_code']:
                    st.warning(f"HTTP Status: {r['status_code']}")
    
    # Summary
    success_count = sum(1 for r in results if r['success'])
    st.markdown("---")
    st.metric("성공률", f"{success_count}/{len(results)}", delta=f"{success_count/len(results)*100:.0f}%")
    
    if success_count == len(results):
        st.success("✅ 모든 테스트 통과! 앱이 정상 작동할 것입니다.")
    elif success_count > 0:
        st.warning(f"⚠️ 일부 테스트 실패 ({success_count}/{len(results)}). 일부 기능이 작동하지 않을 수 있습니다.")
    else:
        st.error("❌ 모든 테스트 실패. 다음 금융에 접속할 수 없습니다.")
        st.info("해결 방법은 STREAMLIT_CLOUD_DEBUG.md 문서를 참조하세요.")

# System info
st.markdown("---")
st.header("🖥️ 시스템 정보")

col1, col2 = st.columns(2)

with col1:
    st.subheader("환경 변수")
    import os
    env_vars = ["DEBUG_MODE", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            display_value = value[:10] + "..." if len(value) > 10 else value
            st.text(f"{var}: {display_value}")
        else:
            st.text(f"{var}: ❌ 미설정")

with col2:
    st.subheader("HTTP 설정")
    st.text(f"Timeout: {DEFAULT_TIMEOUT}초")
    st.text(f"User-Agent: {DEFAULT_HEADERS['User-Agent'][:50]}...")
    
    # Test session
    session = get_session()
    st.text(f"Session: {'✅ 활성' if session else '❌ 비활성'}")

# Headers
st.markdown("---")
with st.expander("📋 HTTP 헤더 전체 보기"):
    st.json(DEFAULT_HEADERS)
