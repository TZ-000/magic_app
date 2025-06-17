import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pickle
import os

# 데이터 파일 경로
DATA_FILE = "card_magic_data.pkl"

# 데이터 저장 함수
def save_data():
    """모든 세션 데이터를 파일에 저장"""
    data = {
        'card_collection': st.session_state.card_collection,
        'wishlist': st.session_state.wishlist,
        'magic_list': st.session_state.magic_list,
        'manufacturers': st.session_state.manufacturers,
        'magic_genres': st.session_state.magic_genres
    }
    with open(DATA_FILE, 'wb') as f:
        pickle.dump(data, f)

# 데이터 로드 함수
def load_data():
    """파일에서 데이터를 불러와서 세션 상태에 설정"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'rb') as f:
                data = pickle.load(f)
            
            st.session_state.card_collection = data.get('card_collection', pd.DataFrame(columns=[
                '카드명', '구매가격($)', '현재가격($)', '제조사', '단종여부', '개봉여부',
                '판매사이트', '디자인별점', '피니시', '디자인스타일'
            ]))
            st.session_state.wishlist = data.get('wishlist', pd.DataFrame(columns=[
                '이름', '타입', '가격($)', '판매사이트', '우선순위', '비고'
            ]))
            st.session_state.magic_list = data.get('magic_list', pd.DataFrame(columns=[
                '마술명', '장르', '신기함정도', '난이도', '관련영상', '비고'
            ]))
            st.session_state.manufacturers = data.get('manufacturers', [
                "Bicycle", "Theory11", "Ellusionist", "D&D", "Fontaine", 
                "Art of Play", "Kings Wild Project", "USPCC", "Cartamundi"
            ])
            st.session_state.magic_genres = data.get('magic_genres', [
                "카드-세팅", "카드-즉석", "동전", "멘탈리즘", "클로즈업-세팅", 
                "클로즈업-즉석", "일상 즉석", "스테이지", "레스토레이션"
            ])
            return True
        except Exception as e:
            st.error(f"데이터 로드 중 오류 발생: {str(e)}")
            return False
    return False

# 페이지 설정
st.set_page_config(
    page_title="Card Collection & Magic Manager",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사용자 정의 CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 3px solid #3498db;
        padding-bottom: 0.5rem;
    }
    
    .sub-section-header {
        font-size: 1.4rem;
        font-weight: bold;
        color: #34495e;
        margin: 1rem 0 0.5rem 0;
        border-left: 4px solid #3498db;
        padding-left: 1rem;
        background-color: #f8f9fa;
        padding: 0.5rem 1rem;
        border-radius: 5px;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .card-container {
        background-color: #ffffff;
        border: 1px solid #e1e8ed;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .card-container:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    
    .card-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }

        /* Streamlit 컬럼 스타일링 */
    .card-container .row-widget {
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    .card-container [data-testid="column"] {
        background: transparent !important;
        padding: 0.5rem !important;
        border-radius: 8px;
        margin: 0.2rem 0;
    }
    
    .card-container [data-testid="column"]:nth-child(1) {
        border-left: 3px solid #3498db;
        background-color: #f8f9fa !important;
    }
    
    .card-container [data-testid="column"]:nth-child(2) {
        border-left: 3px solid #27ae60;
        background-color: #f0fff4 !important;
    }
    
    .card-container [data-testid="column"]:nth-child(3) {
        border-left: 3px solid #f39c12;
        background-color: #fffbf0 !important;
    }
    
    .card-container [data-testid="column"]:nth-child(4) {
        border-left: 3px solid #9b59b6;
        background-color: #f8f4ff !important;
    }
    
    .card-container [data-testid="column"]:nth-child(5) {
        border-left: 3px solid #e74c3c;
        background-color: #fff0f0 !important;
        text-align: center;
    }
    
    .filter-section {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    .priority-high { 
        color: #e74c3c; 
        font-weight: bold;
    }
    .priority-medium { 
        color: #f39c12; 
        font-weight: bold;
    }
    .priority-low { 
        color: #95a5a6; 
        font-weight: bold;
    }
    
    .difficulty-bar {
        background-color: #ecf0f1;
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
        margin: 5px 0;
        position: relative;
    }
    
    .difficulty-fill {
        height: 100%;
        background: linear-gradient(90deg, #27ae60, #f1c40f, #e74c3c);
        transition: width 0.5s ease;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    .main .block-container {
        max-width: 1400px;
        padding-left: 2rem;
        padding-right: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# 환율 정보 가져오기 함수
@st.cache_data(ttl=3600)
def get_exchange_rate():
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        data = response.json()
        return data['rates'].get('KRW', 1300)
    except:
        return 1300

# 달러를 원화로 변환하는 함수
def usd_to_krw(usd_amount):
    exchange_rate = get_exchange_rate()
    return usd_amount * exchange_rate

# 별점을 표시하는 함수
def display_stars(rating):
    if pd.isna(rating):
        return ""
    full_stars = int(rating)
    half_star = 1 if rating - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    
    return "⭐" * full_stars + "⭐" * half_star + "☆" * empty_stars

# 카드 상태 아이콘
def get_status_icon(status):
    icons = {
        "미개봉": "📦",
        "개봉": "✅", 
        "새 덱": "⭐"
    }
    return icons.get(status, "❓")

# 우선순위 색상
def get_priority_color(priority):
    if priority >= 4.0:
        return "🔴"
    elif priority >= 2.5:
        return "🟡"
    else:
        return "⚪"

# 난이도 막대 표시
def display_difficulty_bar(difficulty):
    if pd.isna(difficulty):
        return ""
    
    width = (difficulty / 5.0) * 100
    color = "#27ae60" if difficulty <= 2 else "#f1c40f" if difficulty <= 3.5 else "#e74c3c"
    
    return f"""
    <div class="difficulty-bar">
        <div class="difficulty-fill" style="width: {width}%; background-color: {color};"></div>
    </div>
    """

# 세션 상태 초기화
def initialize_session_state():
    # 먼저 파일에서 데이터 로드 시도
    if load_data():
        return
    
    # 파일이 없거나 로드 실패 시 기본값으로 초기화
    if 'card_collection' not in st.session_state:
        st.session_state.card_collection = pd.DataFrame(columns=[
            '카드명', '구매가격($)', '현재가격($)', '제조사', '단종여부', '개봉여부',
            '판매사이트', '디자인별점', '피니시', '디자인스타일'
        ])
    
    if 'wishlist' not in st.session_state:
        st.session_state.wishlist = pd.DataFrame(columns=[
            '이름', '타입', '가격($)', '판매사이트', '우선순위', '비고'
        ])
    
    if 'magic_list' not in st.session_state:
        st.session_state.magic_list = pd.DataFrame(columns=[
            '마술명', '장르', '신기함정도', '난이도', '관련영상', '비고'
        ])
    
    if 'manufacturers' not in st.session_state:
        st.session_state.manufacturers = [
            "Bicycle", "Theory11", "Ellusionist", "D&D", "Fontaine", 
            "Art of Play", "Kings Wild Project", "USPCC", "Cartamundi"
        ]
    
    if 'magic_genres' not in st.session_state:
        st.session_state.magic_genres = [
            "카드-세팅", "카드-즉석", "동전", "멘탈리즘", "클로즈업-세팅", 
            "클로즈업-즉석", "일상 즉석", "스테이지", "레스토레이션"
        ]

# 제조사 추가 함수
def add_manufacturer(new_manufacturer):
    if new_manufacturer and new_manufacturer not in st.session_state.manufacturers:
        st.session_state.manufacturers.append(new_manufacturer)
        st.session_state.manufacturers.sort()

# 장르 추가 함수  
def add_genre(new_genre):
    if new_genre and new_genre not in st.session_state.magic_genres:
        st.session_state.magic_genres.append(new_genre)
        st.session_state.magic_genres.sort()

# 데이터 추가 함수들
def add_card_to_collection():
    new_card = {
        '카드명': st.session_state.new_card_name,
        '구매가격($)': st.session_state.new_card_purchase_price,
        '현재가격($)': st.session_state.new_card_current_price,
        '제조사': st.session_state.selected_manufacturer if st.session_state.manufacturer_option == "기존 선택" else st.session_state.new_manufacturer_input,
        '단종여부': st.session_state.new_card_discontinued,
        '개봉여부': st.session_state.new_card_status,
        '판매사이트': st.session_state.new_card_site,
        '디자인별점': st.session_state.new_card_rating,
        '피니시': st.session_state.new_card_finish,
        '디자인스타일': st.session_state.new_card_style
    }
    
    # 새 제조사 추가
    if st.session_state.manufacturer_option == "새로 추가":
        add_manufacturer(st.session_state.new_manufacturer_input)
        new_card['제조사'] = st.session_state.new_manufacturer_input
    
    st.session_state.card_collection = pd.concat([
        st.session_state.card_collection, 
        pd.DataFrame([new_card])
    ], ignore_index=True)
    save_data()

def add_card_to_wishlist():
    new_wish = {
        '이름': st.session_state.new_wish_name,
        '타입': st.session_state.new_wish_type,
        '가격($)': st.session_state.new_wish_price,
        '판매사이트': st.session_state.new_wish_site,
        '우선순위': st.session_state.new_wish_priority,
        '비고': st.session_state.new_wish_note
    }
    st.session_state.wishlist = pd.concat([
        st.session_state.wishlist, 
        pd.DataFrame([new_wish])
    ], ignore_index=True)
    save_data()

def add_magic():
    new_magic = {
        '마술명': st.session_state.new_magic_name,
        '장르': st.session_state.selected_genre if st.session_state.genre_option == "기존 선택" else st.session_state.new_genre_input,
        '신기함정도': st.session_state.new_magic_rating,
        '난이도': st.session_state.new_magic_difficulty,
        '관련영상': st.session_state.new_magic_video,
        '비고': st.session_state.new_magic_note
    }
    
    # 새 장르 추가
    if st.session_state.genre_option == "새로 추가":
        add_genre(st.session_state.new_genre_input)
        new_magic['장르'] = st.session_state.new_genre_input
    
    st.session_state.magic_list = pd.concat([
        st.session_state.magic_list, 
        pd.DataFrame([new_magic])
    ], ignore_index=True)
    save_data()

# 클릭 가능한 링크 생성
def make_clickable_link(name, url):
    if pd.isna(url) or url == "":
        return name
    return f'<a href="{url}" target="_blank" style="color: #3498db; text-decoration: none; font-weight: bold;">{name}</a>'

# 메인 앱
def main():
    initialize_session_state()
    
    # 메인 헤더
    st.markdown('<h1 class="main-header">🎭 Card Collection & Magic Manager</h1>', unsafe_allow_html=True)
    
    # 사이드바 네비게이션
    st.sidebar.title("📋 Navigation")
    page = st.sidebar.selectbox(
        "페이지 선택",
        ["🏠 Dashboard", "🃏 Card Collection", "💫 Wishlist", "🎩 Magic Tricks"]
    )
    
    if page == "🏠 Dashboard":
        show_enhanced_dashboard()
    elif page == "🃏 Card Collection":
        show_card_collection()
    elif page == "💫 Wishlist":
        show_wishlist()
    elif page == "🎩 Magic Tricks":
        show_magic_tricks()

def show_enhanced_dashboard():
    st.markdown('<h2 class="section-header">📊 Enhanced Dashboard</h2>', unsafe_allow_html=True)
    
    # 메트릭 카드들 - 4개 열
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_cards = len(st.session_state.card_collection)
        st.markdown(f"""
        <div class="metric-card">
            <h3>🃏 보유 카드</h3>
            <h1>{total_cards}</h1>
            <p>개의 카드</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        wishlist_count = len(st.session_state.wishlist)
        st.markdown(f"""
        <div class="metric-card">
            <h3>💫 위시리스트</h3>
            <h1>{wishlist_count}</h1>
            <p>개의 아이템</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        magic_count = len(st.session_state.magic_list)
        st.markdown(f"""
        <div class="metric-card">
            <h3>🎩 마술 개수</h3>
            <h1>{magic_count}</h1>
            <p>개의 마술</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        if not st.session_state.card_collection.empty:
            total_value = st.session_state.card_collection['현재가격($)'].sum()
            total_value_krw = usd_to_krw(total_value)
            st.markdown(f"""
            <div class="metric-card">
                <h3>💰 총 가치</h3>
                <h1>${total_value:.2f}</h1>
                <p>₩{total_value_krw:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <h3>💰 총 가치</h3>
                <h1>$0.00</h1>
                <p>₩0</p>
            </div>
            """, unsafe_allow_html=True)
    
    # 퀵 액션 버튼들 - st.switch_page 대신 세션 상태 사용
    st.markdown('<h3 class="section-header">⚡ Quick Actions</h3>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🃏 카드 추가", key="quick_add_card", use_container_width=True):
            st.session_state.current_page = "🃏 Card Collection"
            st.rerun()
    
    with col2:
        if st.button("💫 위시리스트 추가", key="quick_add_wish", use_container_width=True):
            st.session_state.current_page = "💫 Wishlist"
            st.rerun()
    
    with col3:
        if st.button("🎩 마술 추가", key="quick_add_magic", use_container_width=True):
            st.session_state.current_page = "🎩 Magic Tricks"
            st.rerun()
    
    with col4:
        if st.button("📊 통계 새로고침", key="refresh_stats", use_container_width=True):
            st.rerun()
    
    # 통계 및 인사이트
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h3 class="sub-section-header">📈 컬렉션 통계</h3>', unsafe_allow_html=True)
        
        if not st.session_state.card_collection.empty:
            df = st.session_state.card_collection.copy()
            
            # 개봉 상태별 분포
            if '개봉여부' in df.columns:
                status_dist = df['개봉여부'].value_counts()
                st.write("**📦 개봉 상태별 분포:**")
                for status, count in status_dist.items():
                    icon = get_status_icon(status)
                    st.write(f"{icon} {status}: {count}개")
            
            # 제조사별 분포
            manufacturer_dist = df['제조사'].value_counts().head(5)
            st.write("**🏭 주요 제조사 TOP 5:**")
            for manufacturer, count in manufacturer_dist.items():
                st.write(f"🏷️ {manufacturer}: {count}개")
            
            # 투자 성과
            if '구매가격($)' in df.columns and '현재가격($)' in df.columns:
                total_invested = df['구매가격($)'].sum()
                total_current = df['현재가격($)'].sum()
                if total_invested > 0:
                    roi = ((total_current - total_invested) / total_invested) * 100
                    roi_color = "🟢" if roi >= 0 else "🔴"
                    st.write(f"**💹 총 수익률:** {roi_color} {roi:.2f}%")
        else:
            st.info("📝 아직 카드가 없습니다. 첫 카드를 추가해보세요!")
    
    with col2:
        st.markdown('<h3 class="sub-section-header">🎯 중요한 정보</h3>', unsafe_allow_html=True)
        
        # 높은 우선순위 위시리스트
        if not st.session_state.wishlist.empty:
            high_priority = st.session_state.wishlist[st.session_state.wishlist['우선순위'] >= 4.0]
            if not high_priority.empty:
                st.write("**🔥 높은 우선순위 위시리스트:**")
                for _, item in high_priority.head(5).iterrows():
                    priority_icon = get_priority_color(item['우선순위'])
                    type_icon = "🃏" if item['타입'] == "카드" else "🎩"
                    st.write(f"{priority_icon} {type_icon} {item['이름']} (${item['가격($)']})")
        
        # 최고 평점 마술
        if not st.session_state.magic_list.empty:
            top_magic = st.session_state.magic_list.nlargest(3, '신기함정도')
            st.write("**⭐ 최고 평점 마술 TOP 3:**")
            for _, magic in top_magic.iterrows():
                stars = display_stars(magic['신기함정도'])
                st.write(f"🎩 {magic['마술명']} {stars}")
        
        # 총 위시리스트 가치
        if not st.session_state.wishlist.empty:
            total_wishlist_value = st.session_state.wishlist['가격($)'].sum()
            total_wishlist_krw = usd_to_krw(total_wishlist_value)
            st.write(f"**💫 위시리스트 총 가치:** ${total_wishlist_value:.2f} (₩{total_wishlist_krw:,.0f})")
    
    # 환율 정보 및 유용한 팁
    st.markdown('<h3 class="sub-section-header">💡 유용한 정보</h3>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_rate = get_exchange_rate()
        st.info(f"💱 **현재 환율**\n$1 = ₩{current_rate:,.0f}")
    
    with col2:
        if not st.session_state.card_collection.empty:
            avg_rating = st.session_state.card_collection['디자인별점'].mean()
            st.info(f"⭐ **평균 카드 별점**\n{avg_rating:.1f}/5.0")
        else:
            st.info("⭐ **평균 카드 별점**\n데이터 없음")
    
    with col3:
        if not st.session_state.magic_list.empty:
            avg_difficulty = st.session_state.magic_list['난이도'].mean()
            st.info(f"🎯 **평균 마술 난이도**\n{avg_difficulty:.1f}/5.0")
        else:
            st.info("🎯 **평균 마술 난이도**\n데이터 없음")

def show_card_collection():
    st.markdown('<h2 class="section-header">🃏 Card Collection Management</h2>', unsafe_allow_html=True)
    
    # 카드 추가 섹션
    st.markdown('<h3 class="sub-section-header">➕ 새 카드 추가</h3>', unsafe_allow_html=True)
    with st.expander("카드 정보 입력", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.text_input("카드명", key="new_card_name")
            st.number_input("구매가격($)", min_value=0.0, step=0.01, key="new_card_purchase_price")
            st.number_input("현재가격($)", min_value=0.0, step=0.01, key="new_card_current_price")
        
        with col2:
            st.radio("제조사 선택", ["기존 선택", "새로 추가"], key="manufacturer_option")
            
            if st.session_state.manufacturer_option == "기존 선택":
                st.selectbox("제조사", st.session_state.manufacturers, key="selected_manufacturer")
            else:
                st.text_input("새 제조사명", key="new_manufacturer_input")
            
            st.selectbox("단종여부", ["단종", "현재판매"], key="new_card_discontinued")
            st.selectbox("개봉여부", ["미개봉", "개봉", "새 덱"], key="new_card_status")
        
        with col3:
            st.text_input("판매사이트 URL", key="new_card_site")
            st.slider("디자인별점", 1.0, 5.0, 3.0, 0.5, key="new_card_rating")
            st.selectbox("피니시", ["Standard", "Air Cushion", "Linen", "Smooth", "Embossed"], key="new_card_finish")
            st.selectbox("디자인스타일", ["클래식", "모던", "빈티지", "미니멀", "화려함", "테마"], key="new_card_style")
        
        if st.button("카드 추가", type="primary"):
            if st.session_state.new_card_name:
                add_card_to_collection()
                st.success("✅ 카드가 성공적으로 추가되었습니다!")
                st.rerun()
            else:
                st.error("❌ 카드명을 입력해주세요!")
    
    # 필터링 및 검색 섹션
    st.markdown('<h3 class="sub-section-header">🔍 Filter & Search</h3>', unsafe_allow_html=True)
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            search_term = st.text_input("🔎 카드명 검색")
        
        with col2:
            manufacturer_filter = st.selectbox("제조사 필터", 
                                             ["전체"] + st.session_state.manufacturers)
        
        with col3:
            status_filter = st.selectbox("개봉상태 필터", ["전체", "미개봉", "개봉", "새 덱"])
        
        with col4:
            sort_by = st.selectbox("정렬 기준", ["카드명", "구매가격($)", "현재가격($)", "디자인별점"])
        st.markdown('</div>', unsafe_allow_html=True)
    
# 데이터 필터링 및 정렬
    df = st.session_state.card_collection.copy()
    
    if not df.empty:
        # 검색 필터
        if search_term:
            df = df[df['카드명'].str.contains(search_term, case=False, na=False)]
        
        # 제조사 필터
        if manufacturer_filter != "전체":
            df = df[df['제조사'] == manufacturer_filter]
        
        # 개봉상태 필터
        if status_filter != "전체":
            df = df[df['개봉여부'] == status_filter]
        
        # 정렬
        if not df.empty:
            df = df.sort_values(sort_by, ascending=True)
    
    # 카드 컬렉션 표시
    st.markdown('<h3 class="sub-section-header">📚 Card Collection</h3>', unsafe_allow_html=True)
    
    if not df.empty:
        # 통계 요약
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 카드 수", len(df))
        with col2:
            total_purchase = df['구매가격($)'].sum()
            st.metric("총 구매금액", f"${total_purchase:.2f}")
        with col3:
            total_current = df['현재가격($)'].sum()
            st.metric("현재 총 가치", f"${total_current:.2f}")
        with col4:
            if total_purchase > 0:
                roi = ((total_current - total_purchase) / total_purchase) * 100
                st.metric("수익률", f"{roi:.1f}%", delta=f"{roi:.1f}%")
        
        # 카드 목록 표시 (개선된 버전)
        for idx, row in df.iterrows():
            # 전체 카드를 감싸는 컨테이너
            st.markdown('<div class="card-container">', unsafe_allow_html=True)
            
            # 컬럼 생성
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
            
            with col1:
                st.markdown("### 📋 카드 정보")
                status_icon = get_status_icon(row['개봉여부'])
                st.markdown(f"**{status_icon} {row['카드명']}**")
                st.caption(f"🏭 {row['제조사']} | {row['피니시']} | {row['디자인스타일']}")
            
            with col2:
                st.markdown("### 💰 가격 정보")
                st.write(f"**구매:** ${row['구매가격($)']:.2f}")
                st.write(f"**현재:** ${row['현재가격($)']:.2f}")
                profit = row['현재가격($)'] - row['구매가격($)']
                profit_color = "🟢" if profit >= 0 else "🔴"
                st.write(f"**손익:** {profit_color} ${profit:.2f}")
            
            with col3:
                st.markdown("### ⭐ 평가 정보")
                stars = display_stars(row['디자인별점'])
                st.write(f"**별점:** {stars}")
                discontinued_icon = "❌" if row['단종여부'] == "단종" else "✅"
                st.write(f"**판매상태:** {discontinued_icon} {row['단종여부']}")
            
            with col4:
                st.markdown("### 🔗 구매 링크")
                if pd.notna(row['판매사이트']) and row['판매사이트'] != "":
                    st.markdown(f"[🛒 구매하기]({row['판매사이트']})")
                else:
                    st.write("링크 없음")
            
            with col5:
                st.markdown("### 🛠️ 관리")
                if st.button("🗑️ 삭제", key=f"delete_card_{idx}", help="카드 삭제"):
                    st.session_state.card_collection = st.session_state.card_collection.drop(idx).reset_index(drop=True)
                    save_data()
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")  # 카드 간 구분선
                
    else:
        st.info("🃏 표시할 카드가 없습니다. 필터를 조정하거나 새 카드를 추가해보세요!")

def show_wishlist():
    st.markdown('<h2 class="section-header">💫 Wishlist Management</h2>', unsafe_allow_html=True)
    
    # 위시리스트 아이템 추가 섹션
    st.markdown('<h3 class="sub-section-header">➕ 새 아이템 추가</h3>', unsafe_allow_html=True)
    with st.expander("위시리스트 아이템 입력", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("아이템명", key="new_wish_name")
            st.selectbox("타입", ["카드", "마술용품", "책", "DVD", "기타"], key="new_wish_type")
            st.number_input("예상가격($)", min_value=0.0, step=0.01, key="new_wish_price")
        
        with col2:
            st.text_input("판매사이트 URL", key="new_wish_site")
            st.slider("우선순위", 1.0, 5.0, 3.0, 0.5, key="new_wish_priority")
            st.text_area("비고", key="new_wish_note")
        
        if st.button("위시리스트에 추가", type="primary"):
            if st.session_state.new_wish_name:
                add_card_to_wishlist()
                st.success("✅ 위시리스트에 성공적으로 추가되었습니다!")
                st.rerun()
            else:
                st.error("❌ 아이템명을 입력해주세요!")
    
    # 위시리스트 필터링
    st.markdown('<h3 class="sub-section-header">🔍 Filter & Search</h3>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            wish_search = st.text_input("🔎 아이템명 검색", key="wish_search")
        
        with col2:
            type_filter = st.selectbox("타입 필터", ["전체", "카드", "마술용품", "책", "DVD", "기타"])
        
        with col3:
            priority_filter = st.selectbox("우선순위 필터", ["전체", "높음(4+)", "중간(2-4)", "낮음(~2)"])
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 위시리스트 데이터 필터링
    wish_df = st.session_state.wishlist.copy()
    
    if not wish_df.empty:
        # 검색 필터
        if wish_search:
            wish_df = wish_df[wish_df['이름'].str.contains(wish_search, case=False, na=False)]
        
        # 타입 필터
        if type_filter != "전체":
            wish_df = wish_df[wish_df['타입'] == type_filter]
        
        # 우선순위 필터
        if priority_filter == "높음(4+)":
            wish_df = wish_df[wish_df['우선순위'] >= 4.0]
        elif priority_filter == "중간(2-4)":
            wish_df = wish_df[(wish_df['우선순위'] >= 2.0) & (wish_df['우선순위'] < 4.0)]
        elif priority_filter == "낮음(~2)":
            wish_df = wish_df[wish_df['우선순위'] < 2.0]
        
        # 우선순위 순으로 정렬
        wish_df = wish_df.sort_values('우선순위', ascending=False)
    
    # 위시리스트 표시
    st.markdown('<h3 class="sub-section-header">🛍️ Wishlist Items</h3>', unsafe_allow_html=True)
    
    if not wish_df.empty:
        # 위시리스트 통계
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 아이템 수", len(wish_df))
        with col2:
            total_wishlist_value = wish_df['가격($)'].sum()
            st.metric("총 예상금액", f"${total_wishlist_value:.2f}")
        with col3:
            avg_priority = wish_df['우선순위'].mean()
            st.metric("평균 우선순위", f"{avg_priority:.1f}/5.0")
        with col4:
            high_priority_count = len(wish_df[wish_df['우선순위'] >= 4.0])
            st.metric("높은 우선순위", f"{high_priority_count}개")
        
        # 위시리스트 아이템 표시
        for idx, row in wish_df.iterrows():
            with st.container():
                st.markdown('<div class="card-container">', unsafe_allow_html=True)
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                
                with col1:
                    priority_icon = get_priority_color(row['우선순위'])
                    type_icon = "🃏" if row['타입'] == "카드" else "🎩" if row['타입'] == "마술용품" else "📚" if row['타입'] == "책" else "💿" if row['타입'] == "DVD" else "📦"
                    st.markdown(f"**{priority_icon} {type_icon} {row['이름']}**")
                    st.caption(f"타입: {row['타입']}")
                
                with col2:
                    st.write(f"**가격:** ${row['가격($)']:.2f}")
                    krw_price = usd_to_krw(row['가격($)'])
                    st.caption(f"₩{krw_price:,.0f}")
                
                with col3:
                    priority_stars = "⭐" * int(row['우선순위'])
                    st.write(f"**우선순위:** {priority_stars}")
                    st.write(f"**점수:** {row['우선순위']:.1f}/5.0")
                
                with col4:
                    if pd.notna(row['판매사이트']) and row['판매사이트'] != "":
                        st.markdown(f"[🔗 구매링크]({row['판매사이트']})")
                    else:
                        st.write("링크 없음")
                    
                    if pd.notna(row['비고']) and row['비고'] != "":
                        st.caption(f"💬 {row['비고']}")
                
                with col5:
                    if st.button("🗑️", key=f"delete_wish_{idx}", help="아이템 삭제"):
                        st.session_state.wishlist = st.session_state.wishlist.drop(idx).reset_index(drop=True)
                        save_data()
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("💫 표시할 위시리스트 아이템이 없습니다. 필터를 조정하거나 새 아이템을 추가해보세요!")

def show_magic_tricks():
    st.markdown('<h2 class="section-header">🎩 Magic Tricks Management</h2>', unsafe_allow_html=True)
    
    # 마술 추가 섹션
    st.markdown('<h3 class="sub-section-header">➕ 새 마술 추가</h3>', unsafe_allow_html=True)
    with st.expander("마술 정보 입력", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("마술명", key="new_magic_name")
            
            st.radio("장르 선택", ["기존 선택", "새로 추가"], key="genre_option")
            
            if st.session_state.genre_option == "기존 선택":
                st.selectbox("장르", st.session_state.magic_genres, key="selected_genre")
            else:
                st.text_input("새 장르명", key="new_genre_input")
            
            st.slider("신기함 정도", 1.0, 5.0, 3.0, 0.5, key="new_magic_rating")
        
        with col2:
            st.slider("난이도", 1.0, 5.0, 3.0, 0.5, key="new_magic_difficulty")
            st.text_input("관련 영상 URL", key="new_magic_video")
            st.text_area("비고", key="new_magic_note")
        
        if st.button("마술 추가", type="primary"):
            if st.session_state.new_magic_name:
                add_magic()
                st.success("✅ 마술이 성공적으로 추가되었습니다!")
                st.rerun()
            else:
                st.error("❌ 마술명을 입력해주세요!")
    
    # 마술 필터링
    st.markdown('<h3 class="sub-section-header">🔍 Filter & Search</h3>', unsafe_allow_html=True)
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            magic_search = st.text_input("🔎 마술명 검색", key="magic_search")
        
        with col2:
            genre_filter = st.selectbox("장르 필터", ["전체"] + st.session_state.magic_genres)
        
        with col3:
            difficulty_filter = st.selectbox("난이도 필터", ["전체", "쉬움(~2)", "보통(2-4)", "어려움(4+)"])
        
        with col4:
            rating_filter = st.selectbox("신기함 필터", ["전체", "낮음(~2)", "보통(2-4)", "높음(4+)"])
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 마술 데이터 필터링
    magic_df = st.session_state.magic_list.copy()
    
    if not magic_df.empty:
        # 검색 필터
        if magic_search:
            magic_df = magic_df[magic_df['마술명'].str.contains(magic_search, case=False, na=False)]
        
        # 장르 필터
        if genre_filter != "전체":
            magic_df = magic_df[magic_df['장르'] == genre_filter]
        
        # 난이도 필터
        if difficulty_filter == "쉬움(~2)":
            magic_df = magic_df[magic_df['난이도'] <= 2.0]
        elif difficulty_filter == "보통(2-4)":
            magic_df = magic_df[(magic_df['난이도'] > 2.0) & (magic_df['난이도'] <= 4.0)]
        elif difficulty_filter == "어려움(4+)":
            magic_df = magic_df[magic_df['난이도'] > 4.0]
        
        # 신기함 필터
        if rating_filter == "낮음(~2)":
            magic_df = magic_df[magic_df['신기함정도'] <= 2.0]
        elif rating_filter == "보통(2-4)":
            magic_df = magic_df[(magic_df['신기함정도'] > 2.0) & (magic_df['신기함정도'] <= 4.0)]
        elif rating_filter == "높음(4+)":
            magic_df = magic_df[magic_df['신기함정도'] > 4.0]
        
        # 신기함 정도 순으로 정렬
        magic_df = magic_df.sort_values('신기함정도', ascending=False)
    
    # 마술 목록 표시
    st.markdown('<h3 class="sub-section-header">🎭 Magic Tricks Collection</h3>', unsafe_allow_html=True)
    
    if not magic_df.empty:
        # 마술 통계
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 마술 수", len(magic_df))
        with col2:
            avg_rating = magic_df['신기함정도'].mean()
            st.metric("평균 신기함", f"{avg_rating:.1f}/5.0")
        with col3:
            avg_difficulty = magic_df['난이도'].mean()
            st.metric("평균 난이도", f"{avg_difficulty:.1f}/5.0")
        with col4:
            high_rating_count = len(magic_df[magic_df['신기함정도'] >= 4.0])
            st.metric("고평점 마술", f"{high_rating_count}개")
        
        # 마술 아이템 표시
        for idx, row in magic_df.iterrows():
            with st.container():
                st.markdown('<div class="card-container">', unsafe_allow_html=True)
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                
                with col1:
                    genre_icon = "🃏" if "카드" in row['장르'] else "🪙" if "동전" in row['장르'] else "🧠" if "멘탈" in row['장르'] else "🎭"
                    st.markdown(f"**{genre_icon} {row['마술명']}**")
                    st.caption(f"장르: {row['장르']}")
                
                with col2:
                    amazement_stars = display_stars(row['신기함정도'])
                    st.write(f"**신기함:** {amazement_stars}")
                    st.caption(f"점수: {row['신기함정도']:.1f}/5.0")
                
                with col3:
                    difficulty_color = "#27ae60" if row['난이도'] <= 2 else "#f1c40f" if row['난이도'] <= 3.5 else "#e74c3c"
                    st.write(f"**난이도:** {row['난이도']:.1f}/5.0")
                    st.markdown(display_difficulty_bar(row['난이도']), unsafe_allow_html=True)
                
                with col4:
                    if pd.notna(row['관련영상']) and row['관련영상'] != "":
                        st.markdown(f"[🎥 영상보기]({row['관련영상']})")
                    else:
                        st.write("영상 없음")
                    
                    if pd.notna(row['비고']) and row['비고'] != "":
                        st.caption(f"💬 {row['비고']}")
                
                with col5:
                    if st.button("🗑️", key=f"delete_magic_{idx}", help="마술 삭제"):
                        st.session_state.magic_list = st.session_state.magic_list.drop(idx).reset_index(drop=True)
                        save_data()
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("🎩 표시할 마술이 없습니다. 필터를 조정하거나 새 마술을 추가해보세요!")

# 앱 실행
if __name__ == "__main__":
    main()
