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
       padding: 1rem;
       border-radius: 10px;
       color: white;
       text-align: center;
       margin: 0.5rem;
       box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
   
   .card-link {
       color: #3498db;
       text-decoration: none;
       font-weight: bold;
       cursor: pointer;
   }
   
   .card-link:hover {
       color: #2980b9;
       text-decoration: underline;
   }
   
   .success-message {
       background-color: #d4edda;
       border: 1px solid #c3e6cb;
       color: #155724;
       padding: 1rem;
       border-radius: 5px;
       margin: 1rem 0;
   }
   
   .error-message {
       background-color: #f8d7da;
       border: 1px solid #f5c6cb;
       color: #721c24;
       padding: 1rem;
       border-radius: 5px;
       margin: 1rem 0;
   }
</style>
""", unsafe_allow_html=True)

# 환율 정보 가져오기 함수
@st.cache_data(ttl=3600)  # 1시간 캐시
def get_exchange_rate():
try:
# 실제 환경에서는 API 키가 필요할 수 있습니다
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

# 세션 상태 초기화
def initialize_session_state():
if 'card_collection' not in st.session_state:
st.session_state.card_collection = pd.DataFrame(columns=[
'카드명', '구매가격($)', '현재가격($)', '제조사', '단종여부', 
'판매사이트', '디자인별점', '피니시', '디자인스타일'
])

if 'wishlist' not in st.session_state:
st.session_state.wishlist = pd.DataFrame(columns=[
'카드명', '가격($)', '판매사이트', '우선순위', '비고'
])

if 'magic_list' not in st.session_state:
st.session_state.magic_list = pd.DataFrame(columns=[
'마술명', '장르', '신기함정도', '관련영상', '비고'
])

# 데이터 추가 함수들
def add_card_to_collection():
new_card = {
'카드명': st.session_state.new_card_name,
'구매가격($)': st.session_state.new_card_purchase_price,
'현재가격($)': st.session_state.new_card_current_price,
'제조사': st.session_state.new_card_manufacturer,
'단종여부': st.session_state.new_card_discontinued,
'판매사이트': st.session_state.new_card_site,
'디자인별점': st.session_state.new_card_rating,
'피니시': st.session_state.new_card_finish,
'디자인스타일': st.session_state.new_card_style
}
st.session_state.card_collection = pd.concat([
st.session_state.card_collection, 
pd.DataFrame([new_card])
], ignore_index=True)

def add_card_to_wishlist():
new_wish = {
'카드명': st.session_state.new_wish_name,
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
'장르': st.session_state.new_magic_genre,
'신기함정도': st.session_state.new_magic_rating,
'관련영상': st.session_state.new_magic_video,
'비고': st.session_state.new_magic_note
}
st.session_state.magic_list = pd.concat([
st.session_state.magic_list, 
pd.DataFrame([new_magic])
], ignore_index=True)

# 메인 앱
def main():
initialize_session_state()

# 메인 헤더
st.markdown('<h1 class="main-header">🎭 Card Collection & Magic Manager</h1>', unsafe_allow_html=True)

# 사이드바 네비게이션
st.sidebar.title("📋 Navigation")
page = st.sidebar.selectbox(
"페이지 선택",
["🏠 Dashboard", "🃏 Card Collection", "💫 Wishlist", "🎩 Magic Tricks", "📊 Analytics"]
)

if page == "🏠 Dashboard":
show_dashboard()
elif page == "🃏 Card Collection":
show_card_collection()
elif page == "💫 Wishlist":
show_wishlist()
elif page == "🎩 Magic Tricks":
show_magic_tricks()
elif page == "📊 Analytics":
show_analytics()

def show_dashboard():
st.markdown('<h2 class="section-header">📊 Dashboard Overview</h2>', unsafe_allow_html=True)

# 메트릭 카드들
col1, col2, col3, col4 = st.columns(4)

with col1:
total_cards = len(st.session_state.card_collection)
st.metric("보유 카드 수", total_cards, delta=None)

with col2:
wishlist_count = len(st.session_state.wishlist)
st.metric("위시리스트", wishlist_count, delta=None)

with col3:
magic_count = len(st.session_state.magic_list)
st.metric("마술 개수", magic_count, delta=None)

with col4:
if not st.session_state.card_collection.empty:
total_value = st.session_state.card_collection['현재가격($)'].sum()
st.metric("총 컬렉션 가치($)", f"{total_value:.2f}")
else:
st.metric("총 컬렉션 가치($)", "0.00")

# 최근 활동
st.markdown('<h3 class="section-header">📈 Quick Stats</h3>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
if not st.session_state.card_collection.empty:
st.subheader("💰 가격 상승률 TOP 5")
df = st.session_state.card_collection.copy()
if '구매가격($)' in df.columns and '현재가격($)' in df.columns:
df['상승률(%)'] = ((df['현재가격($)'] - df['구매가격($)']) / df['구매가격($)'] * 100).round(2)
top_gainers = df.nlargest(5, '상승률(%)')
for _, row in top_gainers.iterrows():
st.write(f"🃏 {row['카드명']}: +{row['상승률(%)']}%")

with col2:
if not st.session_state.magic_list.empty:
st.subheader("⭐ 높은 평점 마술 TOP 5")
top_magic = st.session_state.magic_list.nlargest(5, '신기함정도')
for _, row in top_magic.iterrows():
st.write(f"🎩 {row['마술명']}: {display_stars(row['신기함정도'])}")

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
st.selectbox("제조사", 
["Bicycle", "Theory11", "Ellusionist", "Art of Play", "Kings Wild Project", "기타"], 
key="new_card_manufacturer")
st.selectbox("단종여부", ["단종", "현재판매"], key="new_card_discontinued")
st.text_input("판매사이트 URL", key="new_card_site")

with col3:
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
["전체"] + list(st.session_state.card_collection['제조사'].unique()) if not st.session_state.card_collection.empty else ["전체"])

with col3:
discontinued_filter = st.selectbox("단종여부 필터", ["전체", "단종", "현재판매"])

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

# 단종여부 필터
if discontinued_filter != "전체":
df = df[df['단종여부'] == discontinued_filter]

# 정렬
df = df.sort_values(by=sort_by)

# 가격 상승률 계산
df['상승률(%)'] = ((df['현재가격($)'] - df['구매가격($)']) / df['구매가격($)'] * 100).round(2)
df['구매가격(₩)'] = df['구매가격($)'].apply(lambda x: f"{usd_to_krw(x):,.0f}")
df['현재가격(₩)'] = df['현재가격($)'].apply(lambda x: f"{usd_to_krw(x):,.0f}")
df['별점표시'] = df['디자인별점'].apply(display_stars)

# 테이블 표시
st.markdown("### 📋 Card Collection")
st.dataframe(
df[['카드명', '구매가격($)', '구매가격(₩)', '현재가격($)', '현재가격(₩)', 
'상승률(%)', '제조사', '단종여부', '별점표시', '피니시', '디자인스타일']],
use_container_width=True,
height=400
)

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
if st.button("🔄 전체 데이터 초기화", type="secondary"):
if st.button("⚠️ 정말 삭제하시겠습니까?"):
st.session_state.card_collection = pd.DataFrame(columns=[
'카드명', '구매가격($)', '현재가격($)', '제조사', '단종여부', 
'판매사이트', '디자인별점', '피니시', '디자인스타일'
])
st.success("✅ 모든 데이터가 초기화되었습니다!")
st.rerun()
else:
st.info("📝 아직 등록된 카드가 없습니다. 새 카드를 추가해보세요!")

def show_wishlist():
st.markdown('<h2 class="section-header">💫 Wishlist Management</h2>', unsafe_allow_html=True)

# 위시리스트 추가 섹션
with st.expander("➕ 위시리스트 추가", expanded=False):
col1, col2 = st.columns(2)

with col1:
st.text_input("카드명", key="new_wish_name")
st.number_input("가격($)", min_value=0.0, step=0.01, key="new_wish_price")
st.text_input("판매사이트 URL", key="new_wish_site")

with col2:
st.slider("우선순위", 1.0, 5.0, 3.0, 0.5, key="new_wish_priority")
st.text_area("비고", key="new_wish_note")

if st.button("위시리스트 추가", type="primary"):
if st.session_state.new_wish_name:
add_card_to_wishlist()
st.success("✅ 위시리스트에 성공적으로 추가되었습니다!")
st.rerun()
else:
st.error("❌ 카드명을 입력해주세요!")

# 필터링 및 검색
st.markdown("### 🔍 Filter & Search")
col1, col2, col3 = st.columns(3)

with col1:
search_wish = st.text_input("🔎 카드명 검색", key="wish_search")

with col2:
priority_filter = st.selectbox("우선순위 필터", ["전체", "1점", "2점", "3점", "4점", "5점"])

with col3:
sort_wish_by = st.selectbox("정렬 기준", ["카드명", "가격($)", "우선순위"], key="wish_sort")

# 위시리스트 데이터 처리
df_wish = st.session_state.wishlist.copy()

if not df_wish.empty:
# 검색 필터
if search_wish:
df_wish = df_wish[df_wish['카드명'].str.contains(search_wish, case=False, na=False)]

# 우선순위 필터
if priority_filter != "전체":
priority_value = float(priority_filter.replace("점", ""))
df_wish = df_wish[df_wish['우선순위'] == priority_value]

# 정렬
df_wish = df_wish.sort_values(by=sort_wish_by, ascending=False if sort_wish_by == "우선순위" else True)

# 환율 변환 및 별점 표시
df_wish['가격(₩)'] = df_wish['가격($)'].apply(lambda x: f"{usd_to_krw(x):,.0f}")
df_wish['별점표시'] = df_wish['우선순위'].apply(display_stars)

# 테이블 표시
st.markdown("### 💫 Wishlist")
st.dataframe(
df_wish[['카드명', '가격($)', '가격(₩)', '별점표시', '비고']],
use_container_width=True,
height=400
)

# 편집 및 삭제 기능
st.markdown("### ✏️ Edit & Delete")
if not df_wish.empty:
selected_wish = st.selectbox("편집할 카드 선택", df_wish['카드명'].tolist(), key="wish_select")
col1, col2 = st.columns(2)

with col1:
if st.button("🗑️ 선택한 카드 삭제", key="wish_delete"):
st.session_state.wishlist = st.session_state.wishlist[
st.session_state.wishlist['카드명'] != selected_wish
]
st.success(f"✅ '{selected_wish}' 카드가 위시리스트에서 삭제되었습니다!")
st.rerun()

with col2:
if st.button("🃏 컬렉션으로 이동", key="wish_to_collection"):
# 위시리스트에서 컬렉션으로 이동하는 로직
wish_item = st.session_state.wishlist[st.session_state.wishlist['카드명'] == selected_wish].iloc[0]
st.info("📝 컬렉션 추가를 위해 추가 정보를 입력해주세요!")
else:
st.info("📝 아직 위시리스트가 비어있습니다. 원하는 카드를 추가해보세요!")

def show_magic_tricks():
st.markdown('<h2 class="section-header">🎩 Magic Tricks Management</h2>', unsafe_allow_html=True)

# 마술 추가 섹션
with st.expander("➕ 새 마술 추가", expanded=False):
col1, col2 = st.columns(2)

with col1:
st.text_input("마술명", key="new_magic_name")
st.selectbox("장르", 
["카드-세팅", "카드-즉석", "클로즈업-세팅", "클로즈업-즉석", "일상 즉석"], 
key="new_magic_genre")
st.slider("신기함 정도", 1.0, 5.0, 3.0, 0.5, key="new_magic_rating")

with col2:
st.text_input("관련 영상 URL", key="new_magic_video")
st.text_area("비고", key="new_magic_note")

if st.button("마술 추가", type="primary"):
if st.session_state.new_magic_name:
add_magic()
st.success("✅ 마술이 성공적으로 추가되었습니다!")
st.rerun()
else:
st.error("❌ 마술명을 입력해주세요!")

# 필터링 및 검색
st.markdown("### 🔍 Filter & Search")
col1, col2, col3 = st.columns(3)

with col1:
search_magic = st.text_input("🔎 마술명 검색", key="magic_search")

with col2:
genre_filter = st.selectbox("장르 필터", 
["전체"] + list(st.session_state.magic_list['장르'].unique()) if not st.session_state.magic_list.empty else ["전체"])

with col3:
sort_magic_by = st.selectbox("정렬 기준", ["마술명", "장르", "신기함정도"], key="magic_sort")

# 마술 데이터 처리
df_magic = st.session_state.magic_list.copy()

if not df_magic.empty:
# 검색 필터
if search_magic:
df_magic = df_magic[df_magic['마술명'].str.contains(search_magic, case=False, na=False)]

# 장르 필터
if genre_filter != "전체":
df_magic = df_magic[df_magic['장르'] == genre_filter]

# 정렬
df_magic = df_magic.sort_values(by=sort_magic_by, ascending=False if sort_magic_by == "신기함정도" else True)

# 별점 표시
df_magic['별점표시'] = df_magic['신기함정도'].apply(display_stars)

# 테이블 표시
st.markdown("### 🎩 Magic Tricks")
st.dataframe(
df_magic[['마술명', '장르', '별점표시', '비고']],
use_container_width=True,
height=400
)

# 편집 및 삭제 기능
st.markdown("### ✏️ Edit & Delete")
if not df_magic.empty:
selected_magic = st.selectbox("편집할 마술 선택", df_magic['마술명'].tolist(), key="magic_select")
col1, col2 = st.columns(2)

with col1:
if st.button("🗑️ 선택한 마술 삭제", key="magic_delete"):
st.session_state.magic_list = st.session_state.magic_list[
st.session_state.magic_list['마술명'] != selected_magic
]
st.success(f"✅ '{selected_magic}' 마술이 삭제되었습니다!")
st.rerun()

with col2:
# 관련 영상 링크가 있으면 표시
magic_row = df_magic[df_magic['마술명'] == selected_magic]
if not magic_row.empty and magic_row.iloc[0]['관련영상']:
video_url = magic_row.iloc[0]['관련영상']
st.markdown(f"[🎬 관련 영상 보기]({video_url})")
else:
st.info("📝 아직 등록된 마술이 없습니다. 새 마술을 추가해보세요!")

def show_analytics():
    """성과 분석 페이지를 표시합니다."""
    st.header("📈 성과 분석")
    st.markdown('<h2 class="section-header">📊 Analytics & Insights</h2>', unsafe_allow_html=True)

    if not st.session_state.performance_history:
        st.info("아직 플레이 기록이 없습니다. 마술을 연습해보세요!")
        return
    
    # 데이터 준비
    df = pd.DataFrame(st.session_state.performance_history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 기본 통계
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_score = df['score'].mean()
        st.metric("평균 점수", f"{avg_score:.1f}점")
    
    with col2:
        max_score = df['score'].max()
        st.metric("최고 점수", f"{max_score:.1f}점")
    
    with col3:
        total_games = len(df)
        st.metric("총 게임 수", f"{total_games}게임")
    # 카드 컬렉션 분석
    if not st.session_state.card_collection.empty:
        df_cards = st.session_state.card_collection.copy()
        df_cards['상승률(%)'] = ((df_cards['현재가격($)'] - df_cards['구매가격($)']) / df_cards['구매가격($)'] * 100)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 제조사별 카드 분포
            st.subheader("🏭 제조사별 카드 분포")
            manufacturer_counts = df_cards['제조사'].value_counts()
            fig_pie = px.pie(values=manufacturer_counts.values, names=manufacturer_counts.index,
                           title="제조사별 카드 분포")
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        # 투자 성과 분석
        st.subheader("💹 투자 성과 분석")
        total_invested = df_cards['구매가격($)'].sum()
        total_current = df_cards['현재가격($)'].sum()
        total_gain = total_current - total_invested
        total_gain_pct = (total_gain / total_invested * 100) if total_invested > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 투자금액", f"${total_invested:.2f}", f"₩{usd_to_krw(total_invested):,.0f}")
        with col2:
            st.metric("현재 총 가치", f"${total_current:.2f}", f"₩{usd_to_krw(total_current):,.0f}")
        with col3:
            st.metric("총 수익률", f"{total_gain_pct:.2f}%", f"${total_gain:.2f}")
        
        # 상위/하위 수익률 카드
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔥 Top 수익률 카드")
            top_gainers = df_cards.nlargest(5, '상승률(%)')
            for _, row in top_gainers.iterrows():
                st.write(f"🃏 **{row['카드명']}**: +{row['상승률(%)']:.2f}%")
        
        with col2:
            st.subheader("❄️ 손실 카드")
            losers = df_cards[df_cards['상승률(%)'] < 0].nsmallest(5, '상승률(%)')
            if not losers.empty:
                for _, row in losers.iterrows():
                    st.write(f"🃏 **{row['카드명']}**: {row['상승률(%)']:.2f}%")
            else:
                st.write("🎉 손실을 본 카드가 없습니다!")

    with col4:
        success_rate = (df['score'] >= 80).mean() * 100
        st.metric("성공률 (80점 이상)", f"{success_rate:.1f}%")
    
    # 시간대별 점수 추이
    st.subheader("📊 점수 추이")
    if len(df) > 1:
        fig_line = px.line(
            df, 
            x='timestamp', 
            y='score',
            title='시간별 점수 변화',
            markers=True
        )
        fig_line.update_layout(
            xaxis_title="시간",
            yaxis_title="점수",
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_line, use_container_width=True)
else:
        st.info("점수 추이를 보려면 더 많은 게임이 필요합니다.")
        st.info("📊 카드 컬렉션 데이터가 없어서 분석을 표시할 수 없습니다.")

    # 마술별 성과 분석
    st.subheader("🎭 마술별 성과")
    # 마술 분석
    if not st.session_state.magic_list.empty:
        st.markdown("---")
        st.subheader("🎭 마술 분석")
        
        df_magic = st.session_state.magic_list.copy()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 장르별 마술 분포
            st.subheader("🎪 장르별 마술 분포")
            genre_counts = df_magic['장르'].value_counts()
            fig_magic_pie = px.pie(values=genre_counts.values, names=genre_counts.index,
                                 title="장르별 마술 분포")
            st.plotly_chart(fig_magic_pie, use_container_width=True)
        
        with col2:
            # 신기함 정도 분포
            st.subheader("⭐ 신기함 정도 분포")
            fig_magic_hist = px.histogram(df_magic, x='신기함정도', nbins=10,
                                        title="신기함 정도 히스토그램")
            st.plotly_chart(fig_magic_hist, use_container_width=True)
        
        # 높은 평점 마술 TOP 10
        st.subheader("🌟 높은 평점 마술 TOP 10")
        top_magic = df_magic.nlargest(10, '신기함정도')
        for i, (_, row) in enumerate(top_magic.iterrows(), 1):
            st.write(f"{i}. **{row['마술명']}** ({row['장르']}) - {display_stars(row['신기함정도'])}")

    if len(df) > 0:
        trick_stats = df.groupby('trick').agg({
            'score': ['mean', 'count', 'max'],
            'attempts': 'mean'
        }).round(2)
    # 위시리스트 분석
    if not st.session_state.wishlist.empty:
        st.markdown("---")
        st.subheader("💫 위시리스트 분석")

        # 컬럼명 정리
        trick_stats.columns = ['평균점수', '플레이횟수', '최고점수', '평균시도횟수']
        trick_stats = trick_stats.reset_index()
        df_wish = st.session_state.wishlist.copy()

col1, col2 = st.columns(2)

with col1:
            # 마술별 평균 점수 막대 차트
            fig_bar = px.bar(
                trick_stats,
                x='trick',
                y='평균점수',
                title='마술별 평균 점수',
                color='평균점수',
                color_continuous_scale='RdYlGn'
            )
            fig_bar.update_layout(
                xaxis_title="마술 종류",
                yaxis_title="평균 점수",
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            # 우선순위별 분포
            st.subheader("📊 우선순위별 분포")
            priority_counts = df_wish['우선순위'].value_counts().sort_index()
            fig_priority = px.bar(x=priority_counts.index, y=priority_counts.values,
                                title="우선순위별 위시리스트 분포",
                                labels={'x': '우선순위', 'y': '개수'})
            st.plotly_chart(fig_priority, use_container_width=True)

with col2:
            # 마술별 플레이 횟수 파이 차트
            fig_pie = px.pie(
                trick_stats,
                values='플레이횟수',
                names='trick',
                title='마술별 플레이 비율'
            )
            fig_pie.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # 상세 통계 테이블
        st.subheader("📋 상세 통계")
        st.dataframe(trick_stats, use_container_width=True)
    
    # 성과 히스토리
    st.subheader("🎯 최근 게임 기록")
    recent_df = df.tail(10).copy()
    recent_df['timestamp'] = recent_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
    recent_df = recent_df.rename(columns={
        'timestamp': '날짜/시간',
        'trick': '마술',
        'score': '점수',
        'attempts': '시도횟수'
    })
    st.dataframe(recent_df, use_container_width=True)
    
    # 학습 추천
    st.subheader("💡 학습 추천")
    if len(df) >= 5:
        # 가장 낮은 점수의 마술 찾기
        lowest_trick = df.groupby('trick')['score'].mean().idxmin()
        lowest_score = df.groupby('trick')['score'].mean().min()
        
        if lowest_score < 70:
            st.warning(f"**{lowest_trick}** 마술의 평균 점수가 {lowest_score:.1f}점으로 낮습니다. 더 연습해보세요!")
            # 가격 분포
            st.subheader("💰 가격 분포")
            fig_price_dist = px.histogram(df_wish, x='가격($)', nbins=15,
                                        title="위시리스트 가격 분포")
            st.plotly_chart(fig_price_dist, use_container_width=True)
        
        # 총 위시리스트 가치
        total_wishlist_value = df_wish['가격($)'].sum()
        st.metric("총 위시리스트 가치", f"${total_wishlist_value:.2f}", f"₩{usd_to_krw(total_wishlist_value):,.0f}")
        
        # 높은 우선순위 위시리스트
        st.subheader("🎯 높은 우선순위 위시리스트")
        high_priority = df_wish[df_wish['우선순위'] >= 4.0].sort_values('우선순위', ascending=False)
        if not high_priority.empty:
            for _, row in high_priority.iterrows():
                st.write(f"🃏 **{row['카드명']}** - {display_stars(row['우선순위'])} (${row['가격($)']})")
else:
            st.success("모든 마술에서 좋은 성과를 보이고 있습니다! 👏")
    else:
        st.info("더 많은 게임을 플레이하면 개인화된 학습 추천을 받을 수 있습니다.")
            st.write("높은 우선순위(4점 이상) 위시리스트가 없습니다.")

# 데이터 내보내기/가져오기 기능
def show_data_management():
st.sidebar.markdown("---")
st.sidebar.subheader("📁 데이터 관리")

# 데이터 내보내기
if st.sidebar.button("💾 데이터 내보내기"):
data_export = {
'card_collection': st.session_state.card_collection.to_dict('records'),
'wishlist': st.session_state.wishlist.to_dict('records'),
'magic_list': st.session_state.magic_list.to_dict('records'),
'export_date': datetime.now().isoformat()
}

json_data = json.dumps(data_export, ensure_ascii=False, indent=2)
st.sidebar.download_button(
label="📥 JSON 파일 다운로드",
data=json_data,
file_name=f"card_magic_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
mime="application/json"
)

# 데이터 가져오기
uploaded_file = st.sidebar.file_uploader("📤 데이터 가져오기", type=['json'])
if uploaded_file is not None:
try:
data_import = json.load(uploaded_file)

st.session_state.card_collection = pd.DataFrame(data_import.get('card_collection', []))
st.session_state.wishlist = pd.DataFrame(data_import.get('wishlist', []))
st.session_state.magic_list = pd.DataFrame(data_import.get('magic_list', []))

st.sidebar.success("✅ 데이터가 성공적으로 가져와졌습니다!")
st.rerun()
except Exception as e:
st.sidebar.error(f"❌ 데이터 가져오기 실패: {str(e)}")

# 추가 유용한 기능들
def show_useful_features():
st.sidebar.markdown("---")
st.sidebar.subheader("🔧 유용한 기능")

# 환율 정보 표시
current_rate = get_exchange_rate()
st.sidebar.info(f"💱 현재 환율: $1 = ₩{current_rate:,.0f}")

# 빠른 통계
if not st.session_state.card_collection.empty:
total_cards = len(st.session_state.card_collection)
avg_rating = st.session_state.card_collection['디자인별점'].mean()
st.sidebar.metric("📊 평균 별점", f"{avg_rating:.1f}/5.0")

# 랜덤 마술 추천
if not st.session_state.magic_list.empty and st.sidebar.button("🎲 랜덤 마술 추천"):
random_magic = st.session_state.magic_list.sample(1).iloc[0]
st.sidebar.success(f"🎩 추천 마술: **{random_magic['마술명']}**")
st.sidebar.write(f"장르: {random_magic['장르']}")
st.sidebar.write(f"평점: {display_stars(random_magic['신기함정도'])}")

# 메인 실행
if __name__ == "__main__":
main()
show_data_management()
show_useful_features()
