import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import requests
import json
import time

# 페이지 설정
st.set_page_config(
    page_title="Magic Collection Manager",
    page_icon="🎴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .card-item {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .priority-high { border-left: 4px solid #FF6B6B; }
    .priority-medium { border-left: 4px solid #FFD93D; }
    .priority-low { border-left: 4px solid #6BCF7F; }
    
    .status-unopened { color: #FF6B6B; font-weight: bold; }
    .status-opened { color: #4ECDC4; font-weight: bold; }
    .status-new { color: #FFD93D; font-weight: bold; }
    
    .genre-card { background-color: #E3F2FD; }
    .genre-closeup { background-color: #F3E5F5; }
    .genre-coin { background-color: #FFF3E0; }
    .genre-mentalism { background-color: #E8F5E8; }
    .genre-other { background-color: #FAFAFA; }
    
    .clickable-link {
        color: #1f77b4;
        text-decoration: none;
        font-weight: bold;
        cursor: pointer;
    }
    
    .clickable-link:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
def init_session_state():
    if 'cards' not in st.session_state:
        st.session_state.cards = []
    if 'wishlist' not in st.session_state:
        st.session_state.wishlist = []
    if 'magic_tricks' not in st.session_state:
        st.session_state.magic_tricks = []
    if 'custom_manufacturers' not in st.session_state:
        st.session_state.custom_manufacturers = []
    if 'custom_genres' not in st.session_state:
        st.session_state.custom_genres = []
    if 'exchange_rate' not in st.session_state:
        st.session_state.exchange_rate = 1300  # 기본 환율

# 환율 정보 가져오기
@st.cache_data(ttl=3600)  # 1시간 캐시
def get_exchange_rate():
    try:
        # 무료 환율 API 사용
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        data = response.json()
        return data['rates']['KRW']
    except:
        return 1300  # 기본값

# 기본 제조사 목록
DEFAULT_MANUFACTURERS = [
    "Bicycle", "Theory11", "Ellusionist", "Fontaine", "D&D", "Virtuoso", 
    "Anyone", "Riffle Shuffle", "Kings Wild Project", "Art of Play",
    "Murphy's Magic", "Vanishing Inc", "Penguin Magic"
]

# 기본 장르 목록
DEFAULT_GENRES = [
    "카드-세팅", "카드-즉석", "클로즈업-세팅", "클로즈업-즉석", "일상 즉석",
    "동전", "멘탈리즘", "스테이지", "팔러", "스트리트"
]

# 달러를 원화로 변환
def usd_to_krw(usd_amount, rate):
    return usd_amount * rate

# 별점 표시
def show_stars(rating):
    stars = "⭐" * int(rating)
    return stars

# 우선순위 색상
def get_priority_color(priority):
    colors = {"높음": "#FF6B6B", "보통": "#FFD93D", "낮음": "#6BCF7F"}
    return colors.get(priority, "#CCCCCC")

# 카드 추가/편집 폼
def card_form(card_data=None, is_edit=False):
    st.subheader("카드 추가" if not is_edit else "카드 편집")
    
    with st.form("card_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("카드 이름", value=card_data.get('name', '') if card_data else '')
            purchase_price = st.number_input("구매 가격 (USD)", min_value=0.0, step=0.01,
                                           value=card_data.get('purchase_price', 0.0) if card_data else 0.0)
            current_price = st.number_input("현재 가격 (USD)", min_value=0.0, step=0.01,
                                          value=card_data.get('current_price', 0.0) if card_data else 0.0)
            
            # 제조사 선택 (수동 추가 가능)
            all_manufacturers = DEFAULT_MANUFACTURERS + st.session_state.custom_manufacturers
            manufacturer_index = 0
            if card_data and card_data.get('manufacturer') in all_manufacturers:
                manufacturer_index = all_manufacturers.index(card_data.get('manufacturer'))
            
            manufacturer = st.selectbox("제조사", all_manufacturers, index=manufacturer_index)
            new_manufacturer = st.text_input("새 제조사 추가")
            if new_manufacturer and new_manufacturer not in all_manufacturers:
                st.session_state.custom_manufacturers.append(new_manufacturer)
                manufacturer = new_manufacturer
            
            discontinued = st.checkbox("단종 여부",
                                     value=card_data.get('discontinued', False) if card_data else False)
        
        with col2:
            website = st.text_input("판매 사이트 URL", value=card_data.get('website', '') if card_data else '')
            design_rating = st.slider("디자인 별점", 1, 5,
                                    value=card_data.get('design_rating', 3) if card_data else 3)
            finish = st.selectbox("피니시", ["Standard", "Air-Cushion", "Linen", "Smooth", "Embossed", "Plastic"],
                                index=["Standard", "Air-Cushion", "Linen", "Smooth", "Embossed", "Plastic"].index(
                                    card_data.get('finish', 'Standard')) if card_data else 0)
            design_style = st.selectbox("디자인 스타일", 
                                      ["Classic", "Modern", "Vintage", "Minimalist", "Artistic", "Custom"],
                                      index=["Classic", "Modern", "Vintage", "Minimalist", "Artistic", "Custom"].index(
                                          card_data.get('design_style', 'Classic')) if card_data else 0)
            
            # 개봉 여부 추가
            opening_status = st.selectbox("개봉 여부", ["미개봉", "개봉", "새 덱"],
                                        index=["미개봉", "개봉", "새 덱"].index(
                                            card_data.get('opening_status', '미개봉')) if card_data else 0)
        
        notes = st.text_area("비고", value=card_data.get('notes', '') if card_data else '')
        
        submitted = st.form_submit_button("저장")
        
        if submitted and name:
            card_info = {
                'name': name,
                'purchase_price': purchase_price,
                'current_price': current_price,
                'manufacturer': manufacturer,
                'discontinued': discontinued,
                'website': website,
                'design_rating': design_rating,
                'finish': finish,
                'design_style': design_style,
                'opening_status': opening_status,
                'notes': notes,
                'added_date': card_data.get('added_date', datetime.now().strftime("%Y-%m-%d")) if card_data else datetime.now().strftime("%Y-%m-%d")
            }
            
            if is_edit and card_data:
                # 편집 모드
                index = st.session_state.edit_card_index
                st.session_state.cards[index] = card_info
                del st.session_state.edit_card_index
                st.success("카드가 수정되었습니다!")
            else:
                # 새 카드 추가
                st.session_state.cards.append(card_info)
                st.success("카드가 추가되었습니다!")
            
            st.rerun()

# 위시리스트 추가/편집 폼
def wishlist_form(wish_data=None, is_edit=False):
    st.subheader("위시리스트 추가" if not is_edit else "위시리스트 편집")
    
    with st.form("wishlist_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("이름", value=wish_data.get('name', '') if wish_data else '')
            item_type = st.selectbox("타입", ["카드", "마술"],
                                   index=["카드", "마술"].index(wish_data.get('type', '카드')) if wish_data else 0)
            price = st.number_input("가격 (USD)", min_value=0.0, step=0.01,
                                  value=wish_data.get('price', 0.0) if wish_data else 0.0)
            website = st.text_input("판매 사이트 URL", value=wish_data.get('website', '') if wish_data else '')
        
        with col2:
            priority = st.selectbox("우선순위", ["높음", "보통", "낮음"],
                                  index=["높음", "보통", "낮음"].index(wish_data.get('priority', '보통')) if wish_data else 1)
            rating = st.slider("별점", 1, 5, value=wish_data.get('rating', 3) if wish_data else 3)
            
        notes = st.text_area("비고", value=wish_data.get('notes', '') if wish_data else '')
        
        submitted = st.form_submit_button("저장")
        
        if submitted and name:
            wish_info = {
                'name': name,
                'type': item_type,
                'price': price,
                'website': website,
                'priority': priority,
                'rating': rating,
                'notes': notes,
                'added_date': wish_data.get('added_date', datetime.now().strftime("%Y-%m-%d")) if wish_data else datetime.now().strftime("%Y-%m-%d")
            }
            
            if is_edit and wish_data:
                index = st.session_state.edit_wish_index
                st.session_state.wishlist[index] = wish_info
                del st.session_state.edit_wish_index
                st.success("위시리스트가 수정되었습니다!")
            else:
                st.session_state.wishlist.append(wish_info)
                st.success("위시리스트가 추가되었습니다!")
            
            st.rerun()

# 마술 추가/편집 폼
def magic_form(magic_data=None, is_edit=False):
    st.subheader("마술 추가" if not is_edit else "마술 편집")
    
    with st.form("magic_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("마술 이름", value=magic_data.get('name', '') if magic_data else '')
            
            # 장르 선택 (수동 추가 가능)
            all_genres = DEFAULT_GENRES + st.session_state.custom_genres
            genre_index = 0
            if magic_data and magic_data.get('genre') in all_genres:
                genre_index = all_genres.index(magic_data.get('genre'))
            
            genre = st.selectbox("마술 장르", all_genres, index=genre_index)
            new_genre = st.text_input("새 장르 추가")
            if new_genre and new_genre not in all_genres:
                st.session_state.custom_genres.append(new_genre)
                genre = new_genre
            
            amazement_rating = st.slider("신기함 정도", 1, 5,
                                       value=magic_data.get('amazement_rating', 3) if magic_data else 3)
            difficulty_rating = st.slider("난이도", 1, 5,
                                        value=magic_data.get('difficulty_rating', 3) if magic_data else 3)
        
        with col2:
            video_url = st.text_input("관련 영상 URL", value=magic_data.get('video_url', '') if magic_data else '')
            performance_time = st.number_input("연행 시간 (분)", min_value=0.0, step=0.5,
                                             value=magic_data.get('performance_time', 0.0) if magic_data else 0.0)
            props_needed = st.text_input("필요한 도구", value=magic_data.get('props_needed', '') if magic_data else '')
            audience_size = st.selectbox("적합한 관객 수", ["1명", "2-5명", "5-10명", "10명 이상", "무관"],
                                       index=["1명", "2-5명", "5-10명", "10명 이상", "무관"].index(
                                           magic_data.get('audience_size', '무관')) if magic_data else 4)
        
        notes = st.text_area("비고", value=magic_data.get('notes', '') if magic_data else '')
        
        submitted = st.form_submit_button("저장")
        
        if submitted and name:
            magic_info = {
                'name': name,
                'genre': genre,
                'amazement_rating': amazement_rating,
                'difficulty_rating': difficulty_rating,
                'video_url': video_url,
                'performance_time': performance_time,
                'props_needed': props_needed,
                'audience_size': audience_size,
                'notes': notes,
                'added_date': magic_data.get('added_date', datetime.now().strftime("%Y-%m-%d")) if magic_data else datetime.now().strftime("%Y-%m-%d")
            }
            
            if is_edit and magic_data:
                index = st.session_state.edit_magic_index
                st.session_state.magic_tricks[index] = magic_info
                del st.session_state.edit_magic_index
                st.success("마술이 수정되었습니다!")
            else:
                st.session_state.magic_tricks.append(magic_info)
                st.success("마술이 추가되었습니다!")
            
            st.rerun()

# 카드 목록 표시
def display_cards():
    if not st.session_state.cards:
        st.info("아직 추가된 카드가 없습니다.")
        return
    
    # 검색 및 필터
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("카드 검색", placeholder="카드 이름으로 검색...")
    with col2:
        status_filter = st.selectbox("개봉 상태 필터", ["전체", "미개봉", "개봉", "새 덱"])
    with col3:
        sort_by = st.selectbox("정렬 기준", ["이름순", "가격순", "별점순", "추가일순"])
    
    # 필터링
    filtered_cards = st.session_state.cards.copy()
    if search_term:
        filtered_cards = [card for card in filtered_cards if search_term.lower() in card['name'].lower()]
    if status_filter != "전체":
        filtered_cards = [card for card in filtered_cards if card['opening_status'] == status_filter]
    
    # 정렬
    if sort_by == "이름순":
        filtered_cards.sort(key=lambda x: x['name'])
    elif sort_by == "가격순":
        filtered_cards.sort(key=lambda x: x['current_price'], reverse=True)
    elif sort_by == "별점순":
        filtered_cards.sort(key=lambda x: x['design_rating'], reverse=True)
    elif sort_by == "추가일순":
        filtered_cards.sort(key=lambda x: x['added_date'], reverse=True)
    
    # 카드 표시
    for i, card in enumerate(filtered_cards):
        original_index = st.session_state.cards.index(card)
        
        with st.container():
            st.markdown('<div class="card-item">', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                # 클릭 가능한 링크로 카드명 표시
                if card['website']:
                    st.markdown(f'<a href="{card["website"]}" target="_blank" class="clickable-link">📰 {card["name"]}</a>', 
                              unsafe_allow_html=True)
                else:
                    st.markdown(f"**{card['name']}**")
                
                # 상태 표시
                status_icon = {"미개봉": "📦", "개봉": "✅", "새 덱": "⭐"}
                st.markdown(f"{status_icon[card['opening_status']]} {card['opening_status']}")
                
                st.markdown(f"**제조사:** {card['manufacturer']}")
                if card['discontinued']:
                    st.markdown("🚫 **단종**")
            
            with col2:
                st.markdown(f"**구매가:** ${card['purchase_price']:.2f}")
                st.markdown(f"**현재가:** ${card['current_price']:.2f}")
                
                # 환율 계산
                krw_purchase = usd_to_krw(card['purchase_price'], st.session_state.exchange_rate)
                krw_current = usd_to_krw(card['current_price'], st.session_state.exchange_rate)
                st.markdown(f"**현재가(₩):** ₩{krw_current:,.0f}")
            
            with col3:
                st.markdown(f"**디자인:** {show_stars(card['design_rating'])}")
                st.markdown(f"**피니시:** {card['finish']}")
                st.markdown(f"**스타일:** {card['design_style']}")
                if card['notes']:
                    st.markdown(f"**비고:** {card['notes']}")
            
            with col4:
                if st.button("✏️", key=f"edit_card_{original_index}", help="편집"):
                    st.session_state.edit_card_index = original_index
                    st.rerun()
                
                if st.button("🗑️", key=f"delete_card_{original_index}", help="삭제"):
                    st.session_state.cards.pop(original_index)
                    st.success("카드가 삭제되었습니다!")
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")

# 위시리스트 표시
def display_wishlist():
    if not st.session_state.wishlist:
        st.info("아직 추가된 위시리스트가 없습니다.")
        return
    
    # 우선순위별 정렬
    sorted_wishlist = sorted(st.session_state.wishlist, 
                           key=lambda x: {"높음": 3, "보통": 2, "낮음": 1}[x['priority']], 
                           reverse=True)
    
    for i, wish in enumerate(sorted_wishlist):
        original_index = st.session_state.wishlist.index(wish)
        priority_class = f"priority-{wish['priority'].lower()}"
        
        with st.container():
            st.markdown(f'<div class="card-item {priority_class}">', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                # 타입별 아이콘
                type_icon = "🎴" if wish['type'] == "카드" else "🎩"
                
                # 클릭 가능한 링크
                if wish['website']:
                    st.markdown(f'<a href="{wish["website"]}" target="_blank" class="clickable-link">{type_icon} {wish["name"]}</a>', 
                              unsafe_allow_html=True)
                else:
                    st.markdown(f"**{type_icon} {wish['name']}**")
                
                st.markdown(f"**타입:** {wish['type']}")
            
            with col2:
                st.markdown(f"**가격:** ${wish['price']:.2f}")
                krw_price = usd_to_krw(wish['price'], st.session_state.exchange_rate)
                st.markdown(f"**가격(₩):** ₩{krw_price:,.0f}")
            
            with col3:
                # 우선순위 색상 표시
                priority_color = get_priority_color(wish['priority'])
                st.markdown(f'<span style="color: {priority_color}; font-weight: bold;">●</span> **우선순위:** {wish["priority"]}', 
                          unsafe_allow_html=True)
                st.markdown(f"**별점:** {show_stars(wish['rating'])}")
                if wish['notes']:
                    st.markdown(f"**비고:** {wish['notes']}")
            
            with col4:
                if st.button("✏️", key=f"edit_wish_{original_index}", help="편집"):
                    st.session_state.edit_wish_index = original_index
                    st.rerun()
                
                if st.button("🗑️", key=f"delete_wish_{original_index}", help="삭제"):
                    st.session_state.wishlist.pop(original_index)
                    st.success("위시리스트가 삭제되었습니다!")
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")

# 마술 목록 표시
def display_magic_tricks():
    if not st.session_state.magic_tricks:
        st.info("아직 추가된 마술이 없습니다.")
        return
    
    # 신기함 정도순으로 정렬
    sorted_magic = sorted(st.session_state.magic_tricks, 
                         key=lambda x: x['amazement_rating'], reverse=True)
    
    for i, magic in enumerate(sorted_magic):
        original_index = st.session_state.magic_tricks.index(magic)
        
        with st.container():
            st.markdown('<div class="card-item">', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                # 클릭 가능한 링크
                if magic['video_url']:
                    st.markdown(f'<a href="{magic["video_url"]}" target="_blank" class="clickable-link">🎩 {magic["name"]}</a>', 
                              unsafe_allow_html=True)
                else:
                    st.markdown(f"**🎩 {magic['name']}**")
                
                st.markdown(f"**장르:** {magic['genre']}")
                st.markdown(f"**관객 수:** {magic['audience_size']}")
            
            with col2:
                st.markdown(f"**신기함:** {show_stars(magic['amazement_rating'])}")
                
                # 난이도 막대 그래프
                difficulty_bars = "█" * magic['difficulty_rating'] + "░" * (5 - magic['difficulty_rating'])
                st.markdown(f"**난이도:** {difficulty_bars}")
                
                if magic['performance_time'] > 0:
                    st.markdown(f"**연행시간:** {magic['performance_time']}분")
            
            with col3:
                if magic['props_needed']:
                    st.markdown(f"**필요 도구:** {magic['props_needed']}")
                if magic['notes']:
                    st.markdown(f"**비고:** {magic['notes']}")
            
            with col4:
                if st.button("✏️", key=f"edit_magic_{original_index}", help="편집"):
                    st.session_state.edit_magic_index = original_index
                    st.rerun()
                
                if st.button("🗑️", key=f"delete_magic_{original_index}", help="삭제"):
                    st.session_state.magic_tricks.pop(original_index)
                    st.success("마술이 삭제되었습니다!")
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")

# 대시보드
def show_dashboard():
    st.markdown('<h1 class="main-header">🎴 Magic Collection Dashboard</h1>', unsafe_allow_html=True)
    
    # 환율 업데이트
    if st.button("환율 업데이트"):
        st.session_state.exchange_rate = get_exchange_rate()
        st.success(f"환율이 업데이트되었습니다: 1 USD = {st.session_state.exchange_rate:.2f} KRW")
    
    # 전체 통계
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_cards = len(st.session_state.cards)
        st.markdown(f'<div class="metric-card"><h3>{total_cards}</h3><p>총 카드 수</p></div>', unsafe_allow_html=True)
    
    with col2:
        total_value = sum(card['current_price'] for card in st.session_state.cards)
        st.markdown(f'<div class="metric-card"><h3>${total_value:.0f}</h3><p>총 컬렉션 가치</p></div>', unsafe_allow_html=True)
    
    with col3:
        total_magic = len(st.session_state.magic_tricks)
        st.markdown(f'<div class="metric-card"><h3>{total_magic}</h3><p>총 마술 수</p></div>', unsafe_allow_html=True)
    
    with col4:
        total_wishlist = len(st.session_state.wishlist)
        st.markdown(f'<div class="metric-card"><h3>{total_wishlist}</h3><p>위시리스트</p></div>', unsafe_allow_html=True)
    
    if st.session_state.cards:
        # 차트 섹션
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("개봉 상태별 분포")
            status_counts = {}
            for card in st.session_state.cards:
                status = card['opening_status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            fig = px.pie(values=list(status_counts.values()), 
                        names=list(status_counts.keys()),
                        title="카드 개봉 상태")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("제조사별 분포")
            manufacturer_counts = {}
            for card in st.session_state.cards:
                manufacturer = card['manufacturer']
                manufacturer_counts[manufacturer] = manufacturer_counts.get(manufacturer, 0) + 1
            
            fig = px.bar(x=list(manufacturer_counts.keys()), 
                        y=list(manufacturer_counts.values()),
                        title="제조사별 카드 수")
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
     # 디자인 별점 분포
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("디자인 별점 분포")
            rating_counts = {}
            for card in st.session_state.cards:
                rating = card['design_rating']
                rating_counts[f"{rating}⭐"] = rating_counts.get(f"{rating}⭐", 0) + 1
            
            fig = px.bar(x=list(rating_counts.keys()), 
                        y=list(rating_counts.values()),
                        title="디자인 별점별 카드 수")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("가격 분포")
            prices = [card['current_price'] for card in st.session_state.cards]
            fig = px.histogram(x=prices, nbins=10, title="카드 가격 분포 (USD)")
            st.plotly_chart(fig, use_container_width=True)

    # 마술 통계
    if st.session_state.magic_tricks:
        st.subheader("마술 통계")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("장르별 마술 분포")
            genre_counts = {}
            for magic in st.session_state.magic_tricks:
                genre = magic['genre']
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            fig = px.pie(values=list(genre_counts.values()), 
                        names=list(genre_counts.keys()),
                        title="마술 장르별 분포")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("난이도 vs 신기함")
            difficulty = [magic['difficulty_rating'] for magic in st.session_state.magic_tricks]
            amazement = [magic['amazement_rating'] for magic in st.session_state.magic_tricks]
            names = [magic['name'] for magic in st.session_state.magic_tricks]
            
            fig = px.scatter(x=difficulty, y=amazement, text=names,
                           title="마술 난이도 vs 신기함 정도",
                           labels={'x': '난이도', 'y': '신기함 정도'})
            fig.update_traces(textposition="top center")
            st.plotly_chart(fig, use_container_width=True)

# 메인 앱
def main():
    init_session_state()
    
    # 사이드바
    st.sidebar.title("🎴 Navigation")
    
    # 현재 환율 표시
    st.sidebar.markdown(f"**현재 환율:** 1 USD = {st.session_state.exchange_rate:.0f} KRW")
    
    page = st.sidebar.selectbox("페이지 선택", 
                               ["대시보드", "카드 컬렉션", "위시리스트", "마술 목록"])
    
    # 편집 모드 체크
    if 'edit_card_index' in st.session_state:
        st.sidebar.info("카드 편집 모드")
        card_form(st.session_state.cards[st.session_state.edit_card_index], is_edit=True)
        return
    
    if 'edit_wish_index' in st.session_state:
        st.sidebar.info("위시리스트 편집 모드")
        wishlist_form(st.session_state.wishlist[st.session_state.edit_wish_index], is_edit=True)
        return
    
    if 'edit_magic_index' in st.session_state:
        st.sidebar.info("마술 편집 모드")
        magic_form(st.session_state.magic_tricks[st.session_state.edit_magic_index], is_edit=True)
        return
    
    # 페이지별 내용
    if page == "대시보드":
        show_dashboard()
    
    elif page == "카드 컬렉션":
        st.header("🎴 카드 컬렉션")
        
        tab1, tab2 = st.tabs(["카드 목록", "카드 추가"])
        
        with tab1:
            display_cards()
        
        with tab2:
            card_form()
    
    elif page == "위시리스트":
        st.header("💫 위시리스트")
        
        tab1, tab2 = st.tabs(["위시리스트", "아이템 추가"])
        
        with tab1:
            display_wishlist()
        
        with tab2:
            wishlist_form()
    
    elif page == "마술 목록":
        st.header("🎩 마술 목록")
        
        tab1, tab2 = st.tabs(["마술 목록", "마술 추가"])
        
        with tab1:
            display_magic_tricks()
        
        with tab2:
            magic_form()

if __name__ == "__main__":
    main()
