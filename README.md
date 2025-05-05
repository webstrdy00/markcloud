# 상표 검색 API

본 프로젝트는 상표 데이터베이스를 검색하고 필터링하기 위한 RESTful API 서비스입니다. PostgreSQL의 고급 검색 기능을 활용하여 상표명, 출원번호 등으로 효율적인 검색을 지원합니다.

## API 사용법 및 실행 방법

### 환경 설정 및 실행

1. 저장소 클론:

   ```bash
   git clone https://github.com/webstrdy00/markcloud.git
   cd markcloud
   ```

2. 도커 컴포즈를 사용한 실행:

   ```bash
   docker-compose up -d
   ```

   - 기본적으로 PostgreSQL 데이터베이스가 `5432` 포트에서 실행됩니다.
   - pgAdmin은 `5050` 포트에서 `--profile admin` 옵션을 사용할 때만 실행됩니다.

3. 로컬 개발 환경 설정:

   ```bash
   # 가상환경 생성 및 활성화
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

   # 의존성 설치
   pip install -r requirements.txt

   # 애플리케이션 실행
   uvicorn app.main:app --reload
   ```

4. 데이터 로드:

   ```bash
   # 기본 데이터 파일 사용
   python -m app.scripts.load_data

   # 또는 특정 JSON 파일 지정
   python -m app.scripts.load_data /path/to/trademark_data.json
   ```

   - 데이터 로딩 스크립트는 JSON 형식의 상표 데이터를 PostgreSQL 데이터베이스에 적재합니다.
   - 배치 처리 방식으로 대용량 데이터도 효율적으로 처리할 수 있습니다.
   - 전문 검색을 위한 검색 벡터도 자동으로 업데이트됩니다.

### API 엔드포인트

기본 URL: `http://localhost:8000/api/v1`

#### 상표 검색 API

- **GET** `/trademarks`
- **쿼리 파라미터**:

  - `q`: 검색어 (상표명, 출원번호 등)
  - `status`: 상표 등록 상태 필터
  - `product_code`: 상품 분류 코드 필터
  - `from_date`, `to_date`: 날짜 범위 필터 (YYYYMMDD 형식)
  - `date_type`: 날짜 필터 대상 필드 (applicationDate, registrationDate, publicationDate)
  - `offset`: 결과 오프셋 (기본값: 0)
  - `limit`: 페이지당 결과 수 (기본값: 10, 최대: 100)

- **예제 요청**:

  ```
  # 기본 검색
  GET /trademarks?q=스타벅스&limit=20

  # 필터 적용 검색
  GET /trademarks?q=커피&status=등록&product_code=3006&from_date=20200101&to_date=20221231&date_type=applicationDate

  # 한글 초성 검색
  GET /trademarks?q=ㅅㅌㅂㅅ

  # 페이징 처리
  GET /trademarks?q=apple&offset=20&limit=10
  ```

- **응답 형식**:
  ```json
  {
    "total": 125,
    "offset": 0,
    "limit": 10,
    "results": [
      {
        "applicationNumber": "4020200001234",
        "productName": "스타벅스",
        "productNameEng": "STARBUCKS",
        "applicationDate": "20200101",
        "registerStatus": "등록",
        "registrationNumber": ["4012345600000"],
        "registrationDate": ["20201001"],
        "asignProductMainCodeList": ["4303"]
      },
      ...
    ]
  }
  ```

#### 상표 상세 정보 API

- **GET** `/trademarks/{trademark_id}`
- **경로 파라미터**:

  - `trademark_id`: 조회할 상표 ID

- **응답 형식**:
  ```json
  {
    "productName": "스타벅스",
    "productNameEng": "STARBUCKS",
    "applicationNumber": "4020200001234",
    "applicationDate": "20200101",
    "registerStatus": "등록",
    "publicationNumber": "40-2020-0010111",
    "publicationDate": "20200601",
    "registrationNumber": ["4012345600000"],
    "registrationDate": ["20201001"],
    "registrationPubNumber": "40-2020-0020222",
    "registrationPubDate": "20200901",
    "internationalRegNumbers": [],
    "internationalRegDate": null,
    "priorityClaimNumList": [],
    "priorityClaimDateList": [],
    "asignProductMainCodeList": ["4303"],
    "asignProductSubCodeList": ["G4001"],
    "viennaCodeList": ["270501"]
  }
  ```

#### 메타데이터 API

- **GET** `/trademarks/meta/statuses` - 등록 상태 목록

  ```json
  ["등록", "출원", "거절", "소멸", "포기"]
  ```

- **GET** `/trademarks/meta/product-codes` - 상품 분류 코드 목록
  ```json
  ["0101", "0102", "0201", ... ]
  ```

### 스웨거 문서

API 문서는 다음 URL에서 확인할 수 있습니다:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 구현된 기능 설명

### 1. 검색 기능

- **키워드 검색**: 상표명(한글/영문), 출원번호 등으로 검색
- **유사도 기반 검색**: PostgreSQL의 pg_trgm 확장을 활용한 트리그램 유사도 검색
- **한글 초성 검색**: 'ㅅㅂㅅ'로 '스타벅스' 검색 등 초성만으로 검색 가능
  - Python 기반 초성 처리: 데이터베이스와 독립적으로 동작하는 초성 변환 알고리즘 적용
  - 예시: 'ㄱㄱㄹ'로 검색 시 '코카콜라' 등의 결과 검색 가능
- **전문 검색**: tsvector/tsquery를 활용한 효율적인 텍스트 검색

### 2. 필터링 기능

- **등록 상태 필터**: 등록, 출원, 거절, 실효 등 상태별 필터링
- **상품 코드 필터**: 상품 주 분류 코드별 필터링
- **날짜 범위 필터**: 출원일, 등록일, 공고일 등 날짜 범위 필터링
- **페이징 처리**: 대량의 결과를 효율적으로 처리하기 위한 페이징

### 3. 메타데이터 API

- **등록 상태 목록**: 시스템에 등록된 모든 상태값 조회
- **상품 분류 코드**: 시스템에 등록된 모든 상품 분류 코드 조회

## 기술적 의사결정

### 1. PostgreSQL + GIN + pg_trgm 선택 이유

PostgreSQL을 데이터베이스로 선택한 주요 이유는 다음과 같습니다:

- **트리그램 유사도 검색**: pg_trgm 확장을 통해 효율적인 유사도 검색 지원
- **GIN 인덱스 활용**: 전문 검색과 배열 필드 검색을 위한 최적화된 인덱스
- **JSONB 지원**: 리스트 형태의 필드를 효율적으로 저장 및 검색
- **오픈소스 및 확장성**: 무료로 사용 가능하며 다양한 확장 기능 제공

### 2. 계층화된 아키텍처

코드의 가독성, 유지보수성, 확장성을 높이기 위해 계층화된 아키텍처를 적용했습니다:

- **Repository 패턴**: 데이터 액세스 로직을 캡슐화
- **Service 레이어**: 비즈니스 로직 담당
- **Router 레이어**: API 엔드포인트 정의
- **Schema 레이어**: 요청/응답 데이터 검증 및 변환

### 3. 하이브리드 검색 방식

대량 데이터와 검색 품질을 모두 고려한 하이브리드 검색 방식을 채택했습니다:

- **DB 레벨 1차 필터링**: 인덱스를 활용한 고성능 초기 필터링
- **애플리케이션 레벨 후처리**: 결과가 적을 경우 Python 코드로 추가 정렬 및 필터링
- **유틸리티 함수 활용**: 검색어 분석 및 처리를 위한 경량 유틸리티 함수

## 문제 해결 과정에서 고민했던 점

### 1. 한글 초성 검색 구현

한글 초성만으로 검색하는 기능을 구현하기 위해 여러 접근법을 고려했습니다:

- **Python 유틸리티 함수**: 초성 추출 및 매칭 로직을 구현
- **PostgreSQL 함수**: 데이터베이스 레벨에서 초성 추출 함수 구현
- **하이브리드 접근법**: Python으로 초성 여부 판별 + DB 함수로 매칭

초기에는 하이브리드 방식을 시도했으나, 데이터베이스 함수 의존성으로 인한 이식성 문제가 발생했습니다. 최종적으로 순수 Python 기반 구현을 채택했습니다:

1. **초성 검색 감지**: 입력된 검색어가 모두 한글 초성인지 확인
2. **전체 데이터셋 로드**: 효과적인 초성 검색을 위해 큰 범위의 데이터를 가져옴
3. **Python 기반 필터링**: `extract_initial_consonants` 함수로 각 상표명의 초성을 추출하고 검색어와 일치하는지 확인
4. **결과 정제**: 매칭된 결과를 필터링하고 페이징 처리

이 접근법의 장점은 데이터베이스 환경에 관계없이 동일하게 작동하며, 초성 추출 알고리즘을 애플리케이션 레벨에서 쉽게 개선할 수 있다는 점입니다.

### 2. 퍼지 검색과 정확도 균형

검색의 정확도와 유연성 사이의 균형을 맞추기 위해 다양한 접근법을 실험했습니다:

- **트리그램 유사도**: 오타나 부분 일치에도 검색 결과를 제공
- **전문 검색**: 키워드 기반의 정확한 검색 지원
- **유사도 임계값**: 적절한 유사도 임계값(0.3)을 설정하여 정확도 조정
- **유사도 기반 정렬**: 가장 관련성 높은 결과가 상위에 노출되도록 구현

### 3. 대용량 데이터 처리 방안

10만 건 이상의 데이터를 효율적으로 처리하기 위한 전략을 수립했습니다:

- **인덱스 최적화**: GIN 인덱스, B-tree 인덱스 등 적절한 인덱스 설계
- **페이징 처리**: 대량의 결과를 관리 가능한 크기로 분할
- **배치 처리**: 데이터 로딩 시 배치 처리로 메모리 사용량 최적화
- **쿼리 최적화**: 필터링을 먼저 적용하여 검색 범위 축소

### 4. 배열 필드 처리

상품 코드, 비엔나 코드 등 배열 형태의 필드를 효율적으로 처리하기 위한 방법을 고민했습니다:

- **PostgreSQL 배열 타입**: 배열 데이터를 네이티브하게 저장
- **GIN 인덱스**: 배열 요소 검색을 위한 인덱스 최적화
- **any() 연산자**: 배열 내 요소 검색을 위한 효율적인 연산자 활용
- **unnest() 함수**: 메타데이터 조회 시 배열을 행으로 펼쳐서 처리

## 개선 계획

### 1. 성능 최적화

- **캐싱 레이어**: Redis를 활용한 자주 사용되는 검색 결과 캐싱
- **파티셔닝**: pg_partman을 활용한 테이블 파티셔닝으로 대용량 데이터 처리 개선
- **쿼리 튜닝**: EXPLAIN ANALYZE를 활용한 쿼리 성능 분석 및 최적화

### 2. 검색 품질 개선

- **형태소 분석**: 한국어 형태소 분석을 통한 검색 정확도 향상
- **오타 교정**: 자동 오타 교정 및 추천 검색어 기능 추가
- **유사도 알고리즘 개선**: 다양한 유사도 알고리즘 실험 및 비교

### 3. 초성 검색 최적화

- **초성 인덱스 구축**: 상표명의 초성을 추출하여 별도 컬럼으로 저장하고 인덱스 구축
- **역인덱스 활용**: 초성을 키로 하는 역인덱스를 구축하여 검색 속도 향상
- **병렬 처리**: 대용량 데이터에서 초성 매칭 시 멀티스레드 활용
- **점진적 로딩**: 초기 결과를 빠르게 보여주고 추가 결과를 비동기적으로 로드
- **초성 지능형 캐싱**: 자주 사용되는 초성 패턴에 대한 결과를 우선적으로 캐싱

### 4. 확장성 개선

- **Elasticsearch 연동**: 더 고급 검색 기능이 필요할 경우 Elasticsearch 도입 검토
- **비동기 처리**: 대용량 데이터 처리를 위한 비동기 작업 구현

## 기술 스택

- **Backend**: FastAPI, Pydantic, SQLAlchemy
- **Database**: PostgreSQL, pg_trgm, GIN 인덱스
- **Containerization**: Docker, Docker Compose
- **Testing**: Pytest
- **기타**: Python-dotenv, Logging
