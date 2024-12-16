import requests
from bs4 import BeautifulSoup
import csv
import time
import random
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

BASE_URL = "https://www.alba.co.kr"
CATEGORY_URL = "/story/albastory/StoryList"

def get_post_links(page_url):
    # 글 전체 목록 href값
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        post_links = [urljoin(BASE_URL, post.get('href')) for post in soup.select('li.albanow-table a') if post.get('href')]
        if not post_links:
            print(f"페이지에 게시물이 없습니다: {page_url}")
        return post_links
    except requests.exceptions.RequestException as e:
        print(f"페이지 요청 실패: {e}")
        return []

def scrape_post_detail(driver, post_url, max_retries=3):
    # 상세 페이지 정보
    for attempt in range(max_retries):
        try:
            driver.get(post_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'story-content__title')))

            title = driver.find_element(By.CLASS_NAME, 'story-content__title').text
            content = driver.find_element(By.CLASS_NAME, 'story-view').text
            author = driver.find_element(By.CLASS_NAME, 'story-content__userid').find_element(By.TAG_NAME, 'em').text

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'reply-list-wrap')))

            comments = []
            comment_elements = driver.find_elements(By.CSS_SELECTOR, 'ul.reply-list-wrap li.reply-list')
            for comment in comment_elements:
                author = comment.find_element(By.CSS_SELECTOR, 'div.reply-list__top strong.userId').text
                content = comment.find_element(By.CSS_SELECTOR, 'span.reply-list__detail').text
                comments.append(f"{author}: {content}")

            comments_text = " | ".join(comments) if comments else "댓글 없음"

            return [title, content, author, comments_text]

        except TimeoutException:
            print(f"페이지 로딩 시간 초과: {post_url} (재시도 {attempt + 1}/{max_retries})")
        except NoSuchElementException as e:
            print(f"요소를 찾을 수 없음: {e}, URL: {post_url}")
        except Exception as e:
            print(f"데이터 파싱 오류: {e}, URL: {post_url}")

        if attempt < max_retries - 1:
            time.sleep(2)

    print(f"재시도 횟수 초과: {post_url}")
    return None

def main():
    output_file = 'albastory_posts_with_comments.csv'
    
    driver = webdriver.Chrome() 

    with open(output_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['제목', '내용', '작성자', '댓글'])

        page = int(input("크롤링할 페이지 번호를 입력하세요: "))
        print(f"페이지 {page} 크롤링 중...")
        
        page_url = f"{BASE_URL}{CATEGORY_URL}?page={page}"
        post_links = get_post_links(page_url)

        if not post_links:
            print("게시물이 없습니다. 종료합니다.")
            driver.quit()
            return

        for post_url in post_links:
            print(f"상세 페이지 크롤링: {post_url}")
            data = scrape_post_detail(driver, post_url)

            if data:
                writer.writerow(data)
                print(f"수집 완료 - 제목: {data[0]}")
            else:
                print(f"데이터 수집 실패: {post_url}")

            time.sleep(random.uniform(1, 2))

        print(f"페이지 {page} 크롤링 완료!")
    
    driver.quit()

if __name__ == "__main__":
    main()
