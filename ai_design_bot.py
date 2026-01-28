import streamlit as st
import google.generativeai as genai
import colorsys
import re

# [1. 설정] API 키 입력
genai.configure(api_key="AIzaSyBW_61klH8COUQl-Ty9ZiW6CSFsGXCwdOE")

# [2. 디자인 커스텀 구역] 브라우저 테마 대응 버전
st.set_page_config(page_title="Design System Bot", page_icon="🎨", layout="wide")

# CSS와 HTML을 변수에 담아 깔끔하게 주입합니다.
custom_css = """
    <style>
    /* 1. 제목 스타일 - 핑크색 포인트 유지 */
    .main-title {
        color: #FF4B93;
        font-family: 'Pretendard', sans-serif;
        font-weight: 800;
        text-align: center;
        padding: 30px 0px;
        font-size: 36px;
    }

    /* 2. 컬러 박스 - 투명도를 사용하여 테마(라이트/다크)에 자동 대응 */
    [data-testid="column"] {
        background-color: rgba(128, 128, 128, 0.2); 
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.3);
        text-align: center;
        margin-bottom: 10px;
    }

    /* 3. 컬러 피커 라벨 가독성 보정 */
    .stColorPicker label {
        font-weight: 600;
    }
    </style>
    <h1 class="main-title">🎨 나만의 디자인 시스템 비서</h1>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# [3. 함수] 디자인 시스템 계산 로직
def calculate_palette(hex_code):
    clean_hex = hex_code.strip().replace('#', '').upper()
    if len(clean_hex) != 6:
        if len(clean_hex) == 3: clean_hex = "".join([c*2 for c in clean_hex])
        else: return None, None

    r, g, b = tuple(int(clean_hex[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    
    target_level = int(round(l * 10) * 100)
    if target_level > 900: target_level = 900
    if target_level < 100: target_level = 100
    
    is_exact = abs(l - (target_level / 1000)) < 0.005

    palette = []
    for level in [100, 200, 300, 400, 500, 600, 700, 800, 900]:
        standard_l = level / 1000
        if level == target_level and is_exact:
            final_hex = f"#{clean_hex}"
            label = f"{level} (Original)"
        else:
            rgb = colorsys.hls_to_rgb(h, standard_l, s)
            final_hex = '#{:02x}{:02x}{:02x}'.format(*(int(x * 255) for x in rgb)).upper()
            label = f"{level} (Snap)" if level == target_level else f"{level}"
        palette.append({"level": label, "hex": final_hex})
    return palette, target_level

# [4. 채팅 인터페이스]
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Hex 코드를 입력하거나 질문을 하세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 헥사코드 정규식 검사 (샵 유무 상관없음)
    clean_input = prompt.strip().replace('#', '')
    is_hex = re.fullmatch(r'[0-9a-fA-F]{3}|[0-9a-fA-F]{6}', clean_input)

    response_text = ""
    
    if is_hex:
        palette, target_level = calculate_palette(prompt)
        if palette:
            with st.chat_message("assistant"):
                st.write(f"### 🎯 분석 결과: {target_level}단계 기준")
                cols = st.columns(len(palette))
                for i, item in enumerate(palette):
                    with cols[i]:
                        st.color_picker(label=item['level'], value=item['hex'], key=f"p_{i}_{item['hex']}")
                        st.caption(f"**{item['hex']}**")
                
                response_text = "생성된 시스템 팔레트 값입니다:\n"
                for item in palette:
                    response_text += f"- **{item['level']}**: `{item['hex']}`\n"
                st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
    
    else:
        # 일반 대화 (Gemini)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text
        with st.chat_message("assistant"):
            st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})