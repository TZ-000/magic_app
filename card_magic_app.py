import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

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
    
    .quick-action-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .quick-action-card:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .card-status-unopened { color: #e74c3c; }
    .card-status-opened { color: #f39c12; }
    .card-status-new { color: #27ae60; }
    
    .wishlist-card { background-color: #3498db; color: white; }
    .wishlist-magic { background-color: #9b59b6; color: white; }
    
    .priority-high { background-color: #e74c3c; color: white; }
    .priority-medium { background-color: #f39c12; color: white; }
    .priority-low { background-color: #95a5a6; color: white; }
    
    .clickable-link {
        color: #3498db;
        text-decoration: none;
        font-weight: bold;
        cursor: pointer;
    }
    
    .clickable-link:hover {
        color: #2980b9;
        text-decoration: underline;
    }
    
    .stSelectbox > div > div > select {
        background-color: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 8px;
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
    
    .difficulty-bar {
        background-color: #ecf0f1;
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
        margin: 5px 0;
    }
    
    .difficulty-fill {
        height: 100%;
        background: linear-gradient(90deg, #27ae60, #f1c40f, #e74c3c);
        transition: width 0.5s ease;
    }
</style>
""", unsafe_allow_html=True)

# 환율 정보 가져오기 함수
@st.cache_data(ttl=3600)  # 1시간 캐시
def get_exchange_rate():
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        data = response.json()
        return data['rates'].get('KRW', 1300)  # 기본값 1300원
    except:
        return 1300  # API 실패 시 기본값

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
        return "🔴"  # 높음
    elif priority >= 2.5:
        return "🟡"  # 보통
    else:
        return "⚪"  # 낮음

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
    
    # 제조사 목록 초기화 (기본값 + 사용자 추가)
    if 'manufacturers' not in st.session_state:
        st.session_state.manufacturers = [
            "Bicycle", "Theory11", "Ellusionist", "D&D", "Fontaine", 
            "Art of Play", "Kings Wild Project", "USPCC", "Cartamundi"
        ]
    
    # 마술 장르 목록 초기화
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

# 클릭 가능한 링크 생성
def make_clickable_link(name, url):
    if pd.isna(url) or url == "":
        return name
    return f'<a href="{url}" target="_blank" class="clickable-link">{name}</a>'

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
    
    # 퀵 액션 버튼들
    st.markdown('<h3 class="section-header">⚡ Quick Actions</h3>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🃏 카드 추가", key="quick_add_card", use_container_width=True):
            st.switch_page("🃏 Card Collection")
    
    with col2:
        if st.button("💫 위시리스트 추가", key="quick_add_wish", use_container_width=True):
            st.switch_page("💫 Wishlist")
    
    with col3:
        if st.button("🎩 마술 추가", key="quick_add_magic", use_container_width=True):
            st.switch_page("🎩 Magic Tricks")
    
    with col4:
        if st.button("📊 통계 새로고침", key="refresh_stats", use_container_width=True):
            st.rerun()
    
    # 통계 및 인사이트
    col1, col2 = st.columns(2)
    
    with col1:
        # 컬렉션 통계
        st.markdown('<h3 class="section-header">📈 컬렉션 통계</h3>', unsafe_allow_html=True)
        
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
                total_current = df['현재가격($)'].sum() if '현재가격($)' in df.columns else total_invested
                if total_invested > 0:
                    roi = ((total_current - total_invested) / total_invested) * 100
                    roi_color = "🟢" if roi >= 0 else "🔴"
                    st.write(f"**💹 총 수익률:** {roi_color} {roi:.2f}%")
        else:
            st.info("📝 아직 카드가 없습니다. 첫 카드를 추가해보세요!")
    
    with col2:
        # 최근 활동 및 우선순위
        st.markdown('<h3 class="section-header">🎯 중요한 정보</h3>', unsafe_allow_html=True)
        
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
    st.markdown('<h3 class="section-header">💡 유용한 정보</h3>', unsafe_allow_html=True)
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
    with st.expander("➕ 새 카드 추가", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.text_input("카드명", key="new_card_name")
            st.number_input("구매가격($)", min_value=0.0, step=0.01, key="new_card_purchase_price")
            st.number_input("현재가격($)", min_value=0.0, step=0.01, key="new_card_current_price")
        
        with col2:
            # 제조사 선택 방식
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
    
    # 필터링 및 검색
    st.markdown("### 🔍 Filter & Search")
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
        df = df.sort_values(by=sort_by)
        
        # 표시용 데이터 준비
        df_display = df.copy()
        if '구매가격($)' in df.columns and '현재가격($)' in df.columns:
            df_display['상승률(%)'] = ((df['현재가격($)'] - df['구매가격($)']) / df['구매가격($)'] * 100).round(2)
        df_display['구매가격(₩)'] = df['구매가격($)'].apply(lambda x: f"{usd_to_krw(x):,.0f}")
        df_display['현재가격(₩)'] = df['현재가격($)'].apply(lambda x: f"{usd_to_krw(x):,.0f}")
        df_display['별점표시'] = df['디자인별점'].apply(display_stars)
        df_display['상태아이콘'] = df['개봉여부'].apply(get_status_icon)
        
        # 클릭 가능한 카드명 생성
        df_display['카드명_링크'] = df_display.apply(
            lambda row: make_clickable_link(row['카드명'], row.get('판매사이트', '')), axis=1
        )
        
        # 테이블 표시
        st.markdown("### 📋 Card Collection")
        st.markdown(df_display[['카드명_링크', '상태아이콘', '구매가격($)', '구매가격(₩)', 
                               '현재가격($)', '현재가격(₩)', '상승률(%)', '제조사', '단종여부', '별점표시']].to_html(escape=False), 
                   unsafe_allow_html=True)
        
        # 편집 및 삭제 기능
        st.markdown("### ✏️ Edit & Delete")
        if not df.empty:
            selected_card = st.selectbox("편집할 카드 선택", df['카드명'].tolist())
            col1, col2 = st.columns(2)
                    
            with col1:
                if st.button("🗑️ 선택한 카드 삭제", type="secondary"):
                    st.session_state.card_collection = st.session_state.card_collection[
                        st.session_state.card_collection['카드명'] != selected_card
                    ]
                    st.success(f"✅ '{selected_card}' 카드가 삭제되었습니다!")
                    st.rerun()
                    
            with col2:
                if st.button("🔄 전체 데이터 초기화"):
                    st.warning("⚠️ 이 작업은 되돌릴 수 없습니다!")
                    confirm = st.checkbox("정말로 모든 카드 데이터를 삭제하시겠습니까?")
                    if confirm and st.button("⚠️ 확인 - 전체 삭제"):
                        st.session_state.card_collection = pd.DataFrame(columns=[
                            '카드명', '구매가격($)', '현재가격($)', '제조사', '단종여부', '개봉여부',
                            '판매사이트', '디자인별점', '피니시', '디자인스타일'
                        ])
                        st.success("✅ 모든 카드 데이터가 초기화되었습니다!")
                        st.rerun()
        
        # 데이터 내보내기/가져오기
        st.markdown("### 📤 Import/Export")
        col1, col2 = st.columns(2)
        
        with col1:
            if not st.session_state.card_collection.empty:
                csv = st.session_state.card_collection.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="📥 CSV로 내보내기",
                    data=csv,
                    file_name=f"card_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            uploaded_file = st.file_uploader("📤 CSV 파일 업로드", type=['csv'])
            if uploaded_file is not None:
                try:
                    new_data = pd.read_csv(uploaded_file)
                    if st.button("🔄 데이터 가져오기"):
                        st.session_state.card_collection = new_data
                        st.success("✅ 데이터가 성공적으로 가져와졌습니다!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ 파일 읽기 오류: {str(e)}")
    
    else:
        st.info("📝 아직 카드가 없습니다. 첫 카드를 추가해보세요!")

def show_wishlist():
    st.markdown('<h2 class="section-header">💫 Wishlist Management</h2>', unsafe_allow_html=True)
    
    # 위시리스트 추가 섹션
    with st.expander("➕ 새 위시리스트 추가", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("이름", key="new_wish_name")
            st.selectbox("타입", ["카드", "마술도구", "책", "DVD", "기타"], key="new_wish_type")
            st.number_input("가격($)", min_value=0.0, step=0.01, key="new_wish_price")
        
        with col2:
            st.text_input("판매사이트 URL", key="new_wish_site")
            st.slider("우선순위", 1.0, 5.0, 3.0, 0.5, key="new_wish_priority")
            st.text_area("비고", key="new_wish_note")
        
        if st.button("위시리스트 추가", type="primary"):
            if st.session_state.new_wish_name:
                add_card_to_wishlist()
                st.success("✅ 위시리스트가 성공적으로 추가되었습니다!")
                st.rerun()
            else:
                st.error("❌ 이름을 입력해주세요!")
    
    # 위시리스트 표시
    if not st.session_state.wishlist.empty:
        df = st.session_state.wishlist.copy()
        
        # 필터링
        col1, col2 = st.columns(2)
        with col1:
            type_filter = st.selectbox("타입 필터", ["전체"] + df['타입'].unique().tolist())
        with col2:
            priority_filter = st.selectbox("우선순위 필터", ["전체", "높음(4-5)", "보통(2-4)", "낮음(1-2)"])
        
        # 필터 적용
        if type_filter != "전체":
            df = df[df['타입'] == type_filter]
        
        if priority_filter == "높음(4-5)":
            df = df[df['우선순위'] >= 4.0]
        elif priority_filter == "보통(2-4)":
            df = df[(df['우선순위'] >= 2.0) & (df['우선순위'] < 4.0)]
        elif priority_filter == "낮음(1-2)":
            df = df[df['우선순위'] < 2.0]
        
        # 표시용 데이터 준비
        df_display = df.copy()
        df_display['가격(₩)'] = df['가격($)'].apply(lambda x: f"{usd_to_krw(x):,.0f}")
        df_display['우선순위표시'] = df['우선순위'].apply(get_priority_color)
        df_display['타입아이콘'] = df['타입'].apply(lambda x: {"카드": "🃏", "마술도구": "🎩", "책": "📚", "DVD": "💿", "기타": "📦"}.get(x, "❓"))
        df_display['이름_링크'] = df_display.apply(
            lambda row: make_clickable_link(row['이름'], row.get('판매사이트', '')), axis=1
        )
        
        # 우선순위별 정렬
        df_display = df_display.sort_values('우선순위', ascending=False)
        
        st.markdown("### 💫 Wishlist")
        st.markdown(df_display[['이름_링크', '타입아이콘', '가격($)', '가격(₩)', '우선순위표시', '비고']].to_html(escape=False), 
                   unsafe_allow_html=True)
        
        # 삭제 기능
        selected_wish = st.selectbox("삭제할 위시리스트 선택", df['이름'].tolist())
        if st.button("🗑️ 위시리스트 삭제"):
            st.session_state.wishlist = st.session_state.wishlist[
                st.session_state.wishlist['이름'] != selected_wish
            ]
            st.success(f"✅ '{selected_wish}' 위시리스트가 삭제되었습니다!")
            st.rerun()
    
    else:
        st.info("📝 아직 위시리스트가 없습니다. 첫 위시리스트를 추가해보세요!")

def show_magic_tricks():
    st.markdown('<h2 class="section-header">🎩 Magic Tricks Management</h2>', unsafe_allow_html=True)
    
    # 마술 추가 섹션
    with st.expander("➕ 새 마술 추가", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("마술명", key="new_magic_name")
            
            # 장르 선택 방식
            st.radio("장르 선택", ["기존 선택", "새로 추가"], key="genre_option")
            
            if st.session_state.genre_option == "기존 선택":
                st.selectbox("장르", st.session_state.magic_genres, key="selected_genre")
            else:
                st.text_input("새 장르명", key="new_genre_input")
            
            st.slider("신기함정도", 1.0, 5.0, 3.0, 0.5, key="new_magic_rating")
        
        with col2:
            st.slider("난이도", 1.0, 5.0, 3.0, 0.5, key="new_magic_difficulty")
            st.text_input("관련영상 URL", key="new_magic_video")
            st.text_area("비고", key="new_magic_note")
        
        if st.button("마술 추가", type="primary"):
            if st.session_state.new_magic_name:
                add_magic()
                st.success("✅ 마술이 성공적으로 추가되었습니다!")
                st.rerun()
            else:
                st.error("❌ 마술명을 입력해주세요!")
    
    # 마술 목록 표시
    if not st.session_state.magic_list.empty:
        df = st.session_state.magic_list.copy()
        
        # 필터링
        col1, col2 = st.columns(2)
        with col1:
            genre_filter = st.selectbox("장르 필터", ["전체"] + st.session_state.magic_genres)
        with col2:
            difficulty_filter = st.selectbox("난이도 필터", ["전체", "쉬움(1-2)", "보통(2-4)", "어려움(4-5)"])
        
        # 필터 적용
        if genre_filter != "전체":
            df = df[df['장르'] == genre_filter]
        
        if difficulty_filter == "쉬움(1-2)":
            df = df[df['난이도'] <= 2.0]
        elif difficulty_filter == "보통(2-4)":
            df = df[(df['난이도'] > 2.0) & (df['난이도'] <= 4.0)]
        elif difficulty_filter == "어려움(4-5)":
            df = df[df['난이도'] > 4.0]
        
        # 표시용 데이터 준비
        df_display = df.copy()
        df_display['별점표시'] = df['신기함정도'].apply(display_stars)
        df_display['난이도막대'] = df['난이도'].apply(display_difficulty_bar)
        df_display['마술명_링크'] = df_display.apply(
            lambda row: make_clickable_link(row['마술명'], row.get('관련영상', '')), axis=1
        )
        
        # 신기함정도별 정렬
        df_display = df_display.sort_values('신기함정도', ascending=False)
        
        st.markdown("### 🎩 Magic Tricks List")
        
        # 각 마술을 카드 형태로 표시
        for idx, row in df_display.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    if row.get('관련영상', ''):
                        st.markdown(f"**🎩 [{row['마술명']}]({row['관련영상']})**")
                    else:
                        st.markdown(f"**🎩 {row['마술명']}**")
                    st.write(f"📂 장르: {row['장르']}")
                    if row.get('비고', ''):
                        st.write(f"📝 {row['비고']}")
                
                with col2:
                    st.write("⭐ 신기함")
                    st.write(row['별점표시'])
                
                with col3:
                    st.write("🎯 난이도")
                    st.markdown(row['난이도막대'], unsafe_allow_html=True)
                    st.write(f"{row['난이도']:.1f}/5.0")
                
                st.divider()
        
        # 삭제 기능
        selected_magic = st.selectbox("삭제할 마술 선택", df['마술명'].tolist())
        if st.button("🗑️ 마술 삭제"):
            st.session_state.magic_list = st.session_state.magic_list[
                st.session_state.magic_list['마술명'] != selected_magic
            ]
            st.success(f"✅ '{selected_magic}' 마술이 삭제되었습니다!")
            st.rerun()
    
    else:
        st.info("📝 아직 마술이 없습니다. 첫 마술을 추가해보세요!")

# 앱 실행
if __name__ == "__main__":
    main()
