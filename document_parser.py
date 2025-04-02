import requests
import os
import argparse
import json
from dotenv import load_dotenv
import subprocess

load_dotenv()

# --- Configuration ---
# 도큐먼트 파싱 API 엔드포인트 (수정됨)
UPSTAGE_API_URL = "https://api.upstage.ai/v1/document-digitization"


# --- Helper Function for File Selection ---
def choose_file_macos():
    """macOS에서 네이티브 파일 선택 대화상자를 표시합니다."""
    try:
        script = """
        osascript -e 'tell application "System Events"
            activate
            set filePath to choose file with prompt "문서를 선택하세요"
            return POSIX path of filePath
        end tell'
        """
        result = subprocess.run(script, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return None
        file_path = result.stdout.strip()
        return file_path
    except Exception as e:
        print(f"파일 선택 중 오류 발생: {e}")
        return None


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
    headers = {"Authorization": f"Bearer {api_key}"}
    # 추가 데이터 파라미터 준비
    data = {"ocr": "force", "base64_encoding": "['table']", "model": "document-parse"}
    try:
        # 파일을 바이너리 모드로 열어서 업로드 준비
        with open(file_path, "rb") as f:
            files = {"document": (os.path.basename(file_path), f)}
            # POST 요청 보내기 (data 파라미터 추가)
            response = requests.post(
                UPSTAGE_API_URL, headers=headers, files=files, data=data
            )
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
    # 커맨드라인 인수 처리: 파일명 입력 (선택적)
    parser = argparse.ArgumentParser(
        description="Parse a document using the Upstage Document Parsing API and save the result as JSON."
    )
    parser.add_argument(
        "-f",
        "--filename",
        help="The name of the file to parse. If not provided, a file dialog will open.",
    )
    args = parser.parse_args()

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

    # 파일 경로 설정: 커맨드라인 인수 또는 macOS 파일 선택기
    if args.filename:
        script_directory = os.path.dirname(os.path.abspath(__file__))
        file_to_parse = os.path.join(script_directory, args.filename)
    else:
        # macOS 파일 선택 대화상자 열기
        file_to_parse = choose_file_macos()
        if not file_to_parse:
            print("No file selected. Exiting.")
            exit(0)

    # API 호출하여 JSON 결과 받기
    parsed_result = parse_document_upstage(api_key, file_to_parse)

    # 결과 저장: 입력 파일명에서 확장자를 제거하고 .json으로 저장
    if parsed_result:
        print("\n--- Document Parsing Successful ---")
        # script 디렉토리 내의 output 폴더 경로 설정
        script_directory = os.path.dirname(os.path.abspath(__file__))
        output_directory = os.path.join(script_directory, "output")

        # output 폴더가 없으면 생성
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            print(f"Created output directory: {output_directory}")

        # 파일명 추출 및 output 폴더에 저장할 경로 설정
        base_name = os.path.splitext(os.path.basename(file_to_parse))[0]
        output_filename = os.path.join(output_directory, f"{base_name}.json")

        try:
            with open(output_filename, "w", encoding="utf-8") as out_file:
                json.dump(parsed_result, out_file, indent=4, ensure_ascii=False)
            print(f"JSON result saved to: {output_filename}")
        except Exception as e:
            print(f"Error saving JSON file: {e}")
    else:
        print("\n--- Document Parsing Failed ---")
