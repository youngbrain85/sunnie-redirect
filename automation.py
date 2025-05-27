#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import re
import requests
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='automation_log.txt'
)

logger = logging.getLogger()
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', '%Y-%m-%d %H:%M:%S'))
logger.addHandler(console_handler)

# 웹사이트 URL 정보
LOGIN_URL = "https://pharmesthetic.com/bbs/login.php?url=%2Findex.php%3F"
MYPAGE_URL = "https://pharmesthetic.com/shop/mypage.php"
CUSTOM_URL = "https://pharmesthetic.com/theme/pharms/shop/04/custom.php"

# 로그인 정보 (환경 변수에서 로드)
USERNAME = os.environ.get("PHARMESTHETIC_USERNAME", "emvly84")
PASSWORD = os.environ.get("PHARMESTHETIC_PASSWORD", "0923Kwon!")

# PythonAnywhere 설정
CLOUDFLARE_URL = "https://link.sunniecode.com/api/update"
API_KEY = os.environ.get("PYTHONANYWHERE_API_KEY", "W8L5Yd9KzS7BvQ3XpR2FtE6Hn1Jm4Cg0")

# 설정 변수
CONFIG = {
    'LOGIN_URL': LOGIN_URL,
    'MYPAGE_URL': MYPAGE_URL,
    'CUSTOM_SALE_URL': CUSTOM_URL,
    'USERNAME': USERNAME,
    'PASSWORD': PASSWORD,
    'CATEGORIES': [
        {"url": "https://pharmesthetic.com/shop/product.php?ca_type=1&ca_id=30", "name": "Promotion"},
        {"url": "https://pharmesthetic.com/shop/product.php?ca_type=1&ca_id=j0", "name": "Pharbjet"},
        {"url": "https://pharmesthetic.com/shop/product.php?ca_type=1&ca_id=10", "name": "CONAPIDIL"},
        {"url": "https://pharmesthetic.com/shop/product.php?ca_type=1&ca_id=60", "name": "VIBANQUENTMANKA"},
        {"url": "https://pharmesthetic.com/shop/product.php?ca_type=1&ca_id=h0", "name": "AXENDA"},
        # {"url": "https://pharmesthetic.com/shop/product.php?ca_type=1&ca_id=m0", "name": "CRESCINA"}
    ],
    'SERVER_UPDATE_URL': "https://link.sunniecode.com/api/update",
    'API_KEY': API_KEY,
    'DATA_FILE': 'redirect_data.json',
    'PRODUCT_DATA_FILE': 'product_redirect_data.json'
}

def login(driver):
    """웹사이트 로그인"""
    logger.info("로그인 시도 중...")
    
    try:
        driver.get(CONFIG['LOGIN_URL'])
        time.sleep(1.5)
        
        username_field = driver.find_element(By.ID, "login_id")
        password_field = driver.find_element(By.ID, "login_pw")
        
        username_field.clear()
        username_field.send_keys(CONFIG['USERNAME'])
        password_field.clear()
        password_field.send_keys(CONFIG['PASSWORD'])
        
        login_form = driver.find_element(By.NAME, "flogin")
        login_form.submit()
        time.sleep(2)
        
        # 로그인 확인
        if "login.php" in driver.current_url:
            logger.error("로그인 실패!")
            return False
        
        logger.info("로그인 성공!")
        return True
    except Exception as e:
        logger.error(f"로그인 중 오류: {str(e)}")
        return False

def get_main_referral_link(driver):
    """메인 추천인 링크 수집"""
    logger.info("메인 추천인 링크 수집 중...")
    
    try:
        # 마이페이지로 이동
        driver.get(CONFIG['MYPAGE_URL'])
        time.sleep(2)
        
        # 공유하기 버튼 찾아 클릭 (기존 방식 유지)
        share_button = driver.find_element(By.ID, "share_open")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", share_button)
        time.sleep(0.8)
        driver.execute_script("arguments[0].click();", share_button)
        logger.info("공유하기 버튼 클릭 성공")
        
        # 팝업 대기
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "share_pop"))
        )
        logger.info("공유하기 팝업 표시됨")
        
        # spanFooterUrl 요소의 텍스트 내용 추출 (여러 방법 시도)
        
        # 방법 1: innerHTML 또는 textContent 사용
        script = """
        var element = document.getElementById('spanFooterUrl');
        if (element) {
            return element.textContent || element.innerHTML;
        }
        return null;
        """
        referral_url = driver.execute_script(script)
        
        # 방법 2: 직접 요소 찾아서 text 속성 사용
        if not referral_url or len(referral_url) < 10:
            try:
                footer_url_element = driver.find_element(By.ID, "spanFooterUrl")
                referral_url = footer_url_element.get_attribute("textContent") or footer_url_element.text
            except:
                pass
        
        # 방법 3: 디버깅을 위한 팝업 전체 HTML 출력
        if not referral_url or len(referral_url) < 10:
            try:
                popup_html = driver.find_element(By.ID, "share_pop").get_attribute("outerHTML")
                logger.info(f"팝업 HTML: {popup_html[:500]}...")  # 디버깅용
                
                # 정규식으로 URL 추출 시도
                url_match = re.search(r'https?://pharmesthetic\.com/shop/link\.php\?[^"\'<>\s]+', popup_html)
                if url_match:
                    referral_url = url_match.group(0)
            except:
                pass
        
        if referral_url and len(referral_url) > 10:
            logger.info(f"메인 추천인 URL: {referral_url}")
            return referral_url
        else:
            logger.error("메인 추천인 URL을 찾을 수 없습니다.")
            # 디버깅을 위해 페이지 소스 일부 저장
            with open("debug_popup.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source[:10000])
            logger.info("디버깅을 위해 페이지 소스 일부를 debug_popup.html에 저장했습니다.")
            return None
            
    except Exception as e:
        logger.error(f"메인 추천인 링크 수집 중 오류: {str(e)}")
        return None

def collect_custom_sale_products(driver):
    """맞춤판매 제품 링크 수집 - HTML에서 직접 추출"""
    logger.info("맞춤판매 제품 링크 수집 중...")
    try:
        # 맞춤판매 페이지로 이동
        logger.info("맞춤판매 페이지로 이동합니다...")
        driver.get(CONFIG['CUSTOM_SALE_URL'])
        time.sleep(2)
        
        # 맞춤판매 제품 정보 추출 수정 (HTML 구조에 맞게 수정)
        script = """
        var products = [];
        var productElements = document.querySelectorAll('.custom_box');
        
        for (var i = 0; i < productElements.length; i++) {
            var element = productElements[i];
            var titleElement = element.querySelector('.tit, .title');
            var hiddenSpan = element.querySelector('.btns span[style*="display:none"]');
            
            if (titleElement && hiddenSpan) {
                var productName = titleElement.textContent.trim();
                var shareUrl = hiddenSpan.textContent.trim();
                
                if (shareUrl && shareUrl.includes('pharmesthetic.com/shop/link.php')) {
                    products.push({
                        name: productName,
                        url: shareUrl
                    });
                }
            }
        }
        
        // 디버깅 출력
        console.log("찾은 제품 수: " + products.length);
        
        return products;
        """
        
        custom_products = driver.execute_script(script)
        logger.info(f"JavaScript로 총 {len(custom_products)}개의 맞춤판매 제품을 발견했습니다.")
        
        # 결과가 없는 경우 디버깅 정보 수집
        if not custom_products or len(custom_products) == 0:
            logger.warning("맞춤판매 제품을 발견하지 못했습니다. 페이지 구조를 확인합니다...")
            
            # 페이지 소스 일부 저장
            with open("debug_custom_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source[:20000])
            logger.info("디버깅을 위해 페이지 소스 일부를 debug_custom_page.html에 저장했습니다.")
            
            # 대안 방법: 모든 custom_box 요소 정보 출력
            debug_script = """
            var debug_info = [];
            var boxes = document.querySelectorAll('.custom_box');
            
            for (var i = 0; i < boxes.length; i++) {
                var box = boxes[i];
                var box_data = {
                    'index': i,
                    'data_clid': box.getAttribute('data-clid'),
                    'has_title': box.querySelector('.tit, .title') !== null,
                    'title_text': box.querySelector('.tit, .title') ? box.querySelector('.tit, .title').textContent : 'none',
                    'has_btns': box.querySelector('.btns') !== null,
                    'has_hidden_span': box.querySelector('.btns span[style*="display:none"]') !== null,
                    'btns_html': box.querySelector('.btns') ? box.querySelector('.btns').innerHTML : 'none'
                };
                debug_info.push(box_data);
            }
            
            return debug_info;
            """
            
            debug_data = driver.execute_script(debug_script)
            
            # 디버깅 정보 저장
            with open("debug_custom_boxes.json", "w", encoding="utf-8") as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            logger.info("디버깅 정보를 debug_custom_boxes.json에 저장했습니다.")
            
            # 대체 방법 시도: data-clid 속성으로 각 제품 상세 페이지 접근
            logger.info("대체 방법 시도: data-clid 속성으로 제품 접근...")
            
            # 모든 custom_box 요소의 data-clid 속성 수집
            clid_script = """
            var clids = [];
            var boxes = document.querySelectorAll('.custom_box');
            
            for (var i = 0; i < boxes.length; i++) {
                var clid = boxes[i].getAttribute('data-clid');
                if (clid) {
                    var title = boxes[i].querySelector('.tit, .title');
                    clids.push({
                        'clid': clid,
                        'title': title ? title.textContent.trim() : '제품 ' + (i+1)
                    });
                }
            }
            
            return clids;
            """
            
            clid_data = driver.execute_script(clid_script)
            logger.info(f"data-clid 속성이 있는 제품 {len(clid_data)}개 발견")
            
            # 각 제품 상세페이지 접근하여 공유 링크 가져오기
            custom_product_links = {}
            
            for item in clid_data:
                clid = item['clid']
                title = item['title']
                
                try:
                    # 각 맞춤 제품의 상세 페이지로 이동 (JavaScript로 클릭 이벤트 시뮬레이션)
                    click_script = f"""
                    var box = document.querySelector('.custom_box[data-clid="{clid}"]');
                    if (box) {{
                        box.click();
                        return true;
                    }}
                    return false;
                    """
                    
                    clicked = driver.execute_script(click_script)
                    
                    if clicked:
                        logger.info(f"제품 '{title}' 클릭 성공, 상세 페이지 로딩 중...")
                        time.sleep(1)  # 상세 페이지 로딩 대기
                        
                        # 공유 링크 가져오기
                        get_share_url_script = """
                        var shareUrl = null;
                        
                        // 방법 1: 숨겨진 공유 URL 찾기
                        var hiddenSpan = document.querySelector('.btns span[style*="display:none"]');
                        if (hiddenSpan) {
                            shareUrl = hiddenSpan.textContent.trim();
                        }
                        
                        // 방법 2: 공유 버튼의 onclick 속성에서 추출
                        if (!shareUrl) {
                            var shareButton = document.querySelector('[onclick*="showSharePop"]');
                            if (shareButton) {
                                var match = shareButton.getAttribute('onclick').match(/showSharePop\\('([^']+)'\\)/);
                                if (match && match[1]) {
                                    shareUrl = match[1];
                                }
                            }
                        }
                        
                        return shareUrl;
                        """
                        
                        share_url = driver.execute_script(get_share_url_script)
                        
                        if share_url and 'pharmesthetic.com/shop/link.php' in share_url:
                            custom_product_links[title] = share_url
                            logger.info(f"'{title}' 공유 링크 수집 성공: {share_url[:50]}...")
                        else:
                            logger.warning(f"'{title}' 공유 링크를 찾을 수 없음")
                        
                        # 이전 페이지로 돌아가기
                        driver.back()
                        time.sleep(1)
                    else:
                        logger.warning(f"제품 '{title}' 클릭 실패")
                    
                except Exception as e:
                    logger.error(f"제품 '{title}' 처리 중 오류: {str(e)}")
                    driver.get(CONFIG['CUSTOM_SALE_URL'])  # 오류 시 맞춤판매 페이지로 복귀
                    time.sleep(1)
            
            return custom_product_links
        
        # 정상적으로 결과를 찾은 경우 처리
        custom_product_links = {}
        for product in custom_products:
            product_name = product['name']
            product_url = product['url']
            custom_product_links[product_name] = product_url
            logger.info(f"제품 발견: {product_name} - {product_url[:50]}...")
        
        return custom_product_links
    except Exception as e:
        logger.error(f"맞춤판매 제품 링크 수집 실패: {str(e)}")
        return {}

def collect_product_links(driver):
    """개별 제품 링크 수집 - 실제 페이지네이션 구조에 맞게 최적화"""
    logger.info("개별 제품 링크 수집 중...")
    all_product_links = {}
    
    # 각 카테고리 페이지 방문
    for category in CONFIG['CATEGORIES']:
        logger.info(f"{category['name']} 카테고리 상품 수집 중...")
        category_products = []
        
        try:
            # 첫 페이지 방문
            base_url = category['url']
            driver.get(base_url)
            time.sleep(1.5)  # 페이지 로딩 대기
            
            # 해당 카테고리의 총 페이지 수 확인
            total_pages = 1  # 기본값
            try:
                # 페이지네이션 요소 찾기
                pagination = driver.find_element(By.CSS_SELECTOR, "ul.paging")
                page_links = pagination.find_elements(By.CSS_SELECTOR, "li a")
                
                # 숫자로 된 페이지 링크만 필터링
                page_numbers = []
                for link in page_links:
                    link_text = link.text.strip()
                    if link_text.isdigit():
                        page_numbers.append(int(link_text))
                
                if page_numbers:
                    total_pages = max(page_numbers)
                    logger.info(f"{category['name']} 카테고리는 총 {total_pages}페이지가 있습니다.")
            except NoSuchElementException:
                # 페이지네이션 요소가 없는 경우
                logger.info(f"{category['name']} 카테고리에는 페이지네이션이 없습니다. 단일 페이지로 처리합니다.")
            
            # 각 페이지 처리
            for page_num in range(1, total_pages + 1):
                # 현재 페이지가 첫 페이지가 아니면 해당 페이지로 이동
                if page_num > 1:
                    page_url = f"{base_url}&page={page_num}" if "?" in base_url else f"{base_url}?page={page_num}"
                    logger.info(f"{category['name']} 카테고리 {page_num}/{total_pages} 페이지로 이동: {page_url}")
                    driver.get(page_url)
                    time.sleep(1.5)  # 페이지 로딩 대기
                else:
                    logger.info(f"{category['name']} 카테고리 {page_num}/{total_pages} 페이지 처리 중...")
                
                # 현재 페이지에서 상품 링크 수집
                product_elements = driver.find_elements(By.CSS_SELECTOR, "div.box a")
                page_product_count = 0
                
                for element in product_elements:
                    product_url = element.get_attribute("href")
                    if product_url and "view.php?it_id=" in product_url:
                        # 상품명도 함께 수집
                        try:
                            product_name = element.find_element(By.CSS_SELECTOR, "p.tit").text
                            category_products.append({
                                "name": product_name,
                                "url": product_url
                            })
                            logger.info(f"상품 발견: {product_name} - {product_url}")
                            page_product_count += 1
                        except NoSuchElementException:
                            # 상품명을 찾을 수 없는 경우 스킵
                            continue
                
                logger.info(f"{category['name']} 카테고리 {page_num}페이지에서 {page_product_count}개 상품 발견")
            
            all_product_links[category['name']] = category_products
            logger.info(f"{category['name']} 카테고리에서 총 {len(category_products)}개 상품 링크 수집 완료")
            
        except Exception as e:
            logger.error(f"{category['name']} 카테고리 상품 수집 실패: {str(e)}")
            all_product_links[category['name']] = []
    
    return all_product_links

def collect_product_share_links(driver, product_links):
    """개별 제품 공유 링크 수집 - HTML에서 직접 추출"""
    logger.info("개별 제품 공유 링크 수집 중...")
    product_share_links = {}
    
    # 카테고리별로 제품 공유 링크 수집
    for category, products in product_links.items():
        logger.info(f"{category} 카테고리 제품 공유 링크 수집 중...")
        category_share_links = {}
        
        for product in products:
            product_name = product["name"]
            product_url = product["url"]
            
            try:
                logger.info(f"'{product_name}' 공유 링크 수집 중...")
                driver.get(product_url)
                time.sleep(1)  # 페이지 로딩 대기
                
                # HTML에서 직접 공유 링크 추출 (수정된 방식)
                script = """
                // 방법 1: 숨겨진 공유 URL 찾기
                var hiddenSpan = document.querySelector('.btns span[style*="display:none"]');
                if (hiddenSpan) {
                    return hiddenSpan.textContent.trim();
                }
                
                // 방법 2: 공유 버튼의 onclick 속성에서 추출
                var shareButtons = document.querySelectorAll('[onclick*="showSharePop"]');
                for (var i = 0; i < shareButtons.length; i++) {
                    var button = shareButtons[i];
                    var onclickAttr = button.getAttribute('onclick');
                    var match = onclickAttr.match(/showSharePop\\('([^']+)'\\)/);
                    if (match && match[1]) {
                        return match[1];
                    }
                }
                
                return null;
                """
                
                share_url = driver.execute_script(script)
                
                if share_url:
                    category_share_links[product_name] = share_url
                    logger.info(f"공유 링크 수집 성공: {product_name} - {share_url[:50]}...")
                else:
                    logger.warning(f"공유 링크를 찾을 수 없음: {product_name}")
                
            except Exception as e:
                logger.error(f"'{product_name}' 공유 링크 수집 실패: {str(e)}")
                continue
        
        product_share_links[category] = category_share_links
        logger.info(f"{category} 카테고리 {len(category_share_links)}개 제품 공유 링크 수집 완료")
    
    return product_share_links

def check_deleted_products(current_products, previous_data):
    """삭제된 제품 확인"""
    if not previous_data:
        return set()
    
    # 맞춤판매 제품의 경우
    current_custom_products = set(current_products.keys())
    previous_custom_products = set()
    
    # previous_data 형식에 따라 키 추출 방법이 다를 수 있음
    if isinstance(previous_data, dict) and "custom_products" in previous_data:
        previous_custom_products = set(previous_data["custom_products"].keys())
    
    deleted_products = previous_custom_products - current_custom_products
    
    if deleted_products:
        logger.info(f"삭제된 제품 목록: {', '.join(deleted_products)}")
    
    return deleted_products

def load_previous_data(file_path):
    """이전 데이터 로드"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"기존 데이터 로드: {len(data.get('custom_products', {}))}개의 링크")
            return data
        else:
            logger.info("이전 데이터 파일이 없습니다. 새로 생성합니다.")
            return None
    except Exception as e:
        logger.error(f"이전 데이터 로드 실패: {str(e)}")
        return None

def save_data(data, file_path):
    """데이터 저장"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"데이터를 {file_path}에 저장했습니다.")
        return True
    except Exception as e:
        logger.error(f"데이터 저장 실패: {str(e)}")
        return False

def update_server(data, url, api_key):
    try:
        logger.info(f"Cloudflare 서버에 데이터 업데이트 중...")

        # 먼저 기존 데이터 모두 삭제 (선택사항)
        clear_url = url.replace('/update', '/clear')
        clear_headers = {
            "Content-Type": "application/json",
            "X-API-KEY": api_key
        }
        
        try:
            clear_response = requests.post(clear_url, headers=clear_headers)
            if clear_response.status_code == 200:
                logger.info("기존 데이터 초기화 완료")
        except:
            logger.info("데이터 초기화 스킵")

        # ID 매핑 파일 로드
        id_mapping_file = "product_id_mapping.json"
        try:
            with open(id_mapping_file, 'r', encoding='utf-8') as f:
                id_mapping = json.load(f)
        except:
            id_mapping = {}
        
        # 다음 사용 가능한 ID 찾기
        max_id = 0
        for pid in id_mapping.values():
            if pid.startswith('p') and pid[1:].isdigit():
                max_id = max(max_id, int(pid[1:]))
        next_id = max_id + 1
        
        # 카테고리별 제품 데이터 로드
        product_data = None
        if os.path.exists(CONFIG['PRODUCT_DATA_FILE']):
            try:
                with open(CONFIG['PRODUCT_DATA_FILE'], 'r', encoding='utf-8') as f:
                    product_data = json.load(f)
                logger.info(f"카테고리별 제품 데이터 로드: {sum(len(category) for category in product_data.get('categories', {}).values())}개 제품")
            except Exception as e:
                logger.error(f"카테고리별 제품 데이터 로드 실패: {str(e)}")
        
        # Flask 앱의 예상 형식으로 데이터 변환
        formatted_data = {
            "_metadata": {
                "last_updated": int(time.time()),
                "last_updated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            # 메인 링크 추가
            "main": {
                "url": data["main_referral"],
                "original_name": "메인 추천인 링크"
            }
        }
        
        # 맞춤판매 제품 추가 (이미 수정됨)
        custom_count = 0
        for product_name, product_url in data["custom_products"].items():
            if product_name in id_mapping:
                safe_key = id_mapping[product_name]
            else:
                safe_key = f"p{next_id}"
                id_mapping[product_name] = safe_key
                next_id += 1
            
            formatted_data[safe_key] = {
                "url": product_url,
                "original_name": product_name,
                "type": "custom"
            }
            custom_count += 1
        
        # 카테고리별 제품 추가
        category_count = 0
        if product_data and "categories" in product_data:
            for category_name, products in product_data["categories"].items():
                for product_name, product_url in products.items():
                    # 중복 제품명 처리 - 카테고리명 포함
                    full_product_name = f"{product_name} ({category_name})"
                    
                    # ID 매핑 확인 또는 새로 생성
                    if full_product_name in id_mapping:
                        safe_key = id_mapping[full_product_name]
                    else:
                        safe_key = f"p{next_id}"
                        id_mapping[full_product_name] = safe_key
                        next_id += 1
                    
                    formatted_data[safe_key] = {
                        "url": product_url,
                        "original_name": product_name,  # 원래 이름
                        "display_name": full_product_name,  # 표시용 이름 (카테고리 포함)
                        "type": "product",
                        "category": category_name
                    }
                    category_count += 1
        
        # ID 매핑 저장
        with open(id_mapping_file, 'w', encoding='utf-8') as f:
            json.dump(id_mapping, f, ensure_ascii=False, indent=2)
        
        # 요청 전송
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": api_key
        }
        response = requests.post(url, json=formatted_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"서버 업데이트 성공! {result.get('count', 0)}개의 링크 업데이트됨 (맞춤판매: {custom_count}, 카테고리별: {category_count})")
            
            # 업데이트된 URL 출력
            logger.info("\n=== 성공! 링크 업데이트 완료 ===")
            logger.info("===== 리디렉션 링크 자동화 완료 =====")
            logger.info("\n자동화 완료! 인포크 링크에서 다음 고정 URL을 사용하세요:")
            logger.info(f"- 메인 추천인 링크: https://link.sunniecode.com/main")
            
            # ID 매핑된 모든 제품 출력
            for product_name, product_id in sorted(id_mapping.items(), key=lambda x: int(x[1][1:]) if x[1][1:].isdigit() else 999):
                logger.info(f"- {product_name}: https://link.sunniecode.com/{product_id}")
            
            return True
        else:
            logger.error(f"서버 업데이트 실패: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"서버 통신 오류: {str(e)}")
        return False

def main():
    """메인 함수"""
    logger.info("===== 리디렉션 링크 자동화 시작 =====")
    
    # 웹 드라이버 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # 새로운 헤드리스 모드
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        # 이전 데이터 로드
        previous_data = load_previous_data(CONFIG['DATA_FILE'])
        previous_product_data = load_previous_data(CONFIG['PRODUCT_DATA_FILE'])
        
        # 웹드라이버 초기화
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 로그인
        if not login(driver):
            logger.error("로그인 실패. 프로그램을 종료합니다.")
            return
        
        # 메인 추천인 링크 수집
        main_referral_link = get_main_referral_link(driver)
        if not main_referral_link:
            logger.error("메인 추천인 링크 수집 실패. 프로그램을 종료합니다.")
            return
        
        # 맞춤판매 제품 링크 수집
        custom_product_links = collect_custom_sale_products(driver)
        if not custom_product_links:
            logger.error("맞춤판매 제품 링크 수집 실패.")
        
        # 삭제된 제품 확인
        deleted_products = check_deleted_products(custom_product_links, previous_data)
        
        # 개별 제품 링크 수집
        product_links = collect_product_links(driver)
        
        # 개별 제품 공유 링크 수집
        product_share_links = collect_product_share_links(driver, product_links)
        
        # 데이터 구성
        current_data = {
            "main_referral": main_referral_link,
            "custom_products": custom_product_links,
            "deleted_products": list(deleted_products),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        current_product_data = {
            "categories": product_share_links,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 데이터 저장
        save_data(current_data, CONFIG['DATA_FILE'])
        save_data(current_product_data, CONFIG['PRODUCT_DATA_FILE'])
        
        # 서버 업데이트
        update_server(current_data, CONFIG['SERVER_UPDATE_URL'], CONFIG['API_KEY'])
              
    except Exception as e:
        logger.error(f"오류 발생: {str(e)}")
    finally:
        # 드라이버 종료
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()