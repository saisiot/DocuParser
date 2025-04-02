import requests
import os
import argparse
import json
from dotenv import load_dotenv
import tkinter as tk
from tkinter import filedialog

load_dotenv()

# --- Configuration ---
# 도큐먼트 파싱 API 엔드포인트
UPSTAGE_API_URL = "https://api.upstage.ai/v1/document-ai/document-parsing"

# --- Helper Function for API Call ---
def parse_document_upstage(api_key: str, file_path: str):
    """
    Sends a document to the Upstage Document Parsing API and returns the parsed JSON result.

    Args:
        api_key: Your Upstage API key.
        file_path: The full path to the document file.

    Returns:
        A dictionary containing the parsed data from the API, or None if an error occurs.
    """
    print(f"Attempting to parse document: {file_path}")

    # 파일 존재 여부 확인
    if not os.path.isfile(file_path):
        print(f"Error: File not found at path: {file_path}")
        return None

    # 인증 헤더 준비 (Bearer 토큰 방식)
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        # 파일을 바이너리 모드로 열어서 업로드 준비
        with open(file_path, 'rb') as f:
            files = {
                'document': (os.path.basename(file_path), f)
            }
            # POST 요청 보내기
            response = requests.post(UPSTAGE_API_URL, headers=headers, files=files)
            response.raise_for_status()
            # JSON 결과 반환
            return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        if e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            try:
                print("API Error Response:", e.response.json())
            except json.JSONDecodeError:
                print("API Error Response (non-JSON):", e.response.text)
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    # GUI 루트 창 생성 (필요하지만 표시하지 않음)
    root = tk.Tk()
    root.withdraw()  # 루트 창 숨기기
    
    # API 키 획득: 환경 변수에서 가져오기
    api_key = os.environ.get("UPSTAGE_API_KEY")
    if not api_key:
        print("Warning: UPSTAGE_API_KEY environment variable not found.")
        try:
            api_key = input("Please enter your Upstage API Key: ").strip()
            if not api_key:
                print("Error: API Key cannot be empty.")
                exit(1)
        except EOFError:
            print("\nError: Could not read API key from input.")
            exit(1)
    
    # 커맨드라인 인수 처리: 파일명 입력 (선택적)
    parser = argparse.ArgumentParser(description="Parse a document using the Upstage Document Parsing API and save the result as JSON.")
    parser.add_argument("-f", "--filename", help="The name of the file to parse. If not provided, a file dialog will open.")
    args = parser.parse_args()
    
    # 스크립트 디렉토리 설정
    script_directory = os.path.dirname(os.path.abspath(__file__))
    
    # 파일 경로 설정: 커맨드라인 인수 또는 GUI 파일 선택기
    if args.filename:
        file_to_parse = os.path.join(script_directory, args.filename)
    else:
        # GUI 파일 선택 대화상자 열기
        file_to_parse = filedialog.askopenfilename(
            title="Select a document to parse",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("Word documents", "*.docx"),
                ("Excel files", "*.xlsx"),
                ("All files", "*.*")
            ]
        )
        if not file_to_parse:
            print("No file selected. Exiting.")
            exit(0)
    
    # API 호출하여 JSON 결과 받기
    parsed_result = parse_document_upstage(api_key, file_to_parse)
    
    # 결과 저장: 입력 파일명에서 확장자를 제거하고 .json으로 저장
    if parsed_result:
        print("\n--- Document Parsing Successful ---")
        base_name = os.path.splitext(os.path.basename(file_to_parse))[0]
        output_filename = os.path.join(script_directory, f"{base_name}.json")
        try:
            with open(output_filename, 'w', encoding='utf-8') as out_file:
                json.dump(parsed_result, out_file, indent=4, ensure_ascii=False)
            print(f"JSON result saved to: {output_filename}")
        except Exception as e:
            print(f"Error saving JSON file: {e}")
    else:
        print("\n--- Document Parsing Failed ---")