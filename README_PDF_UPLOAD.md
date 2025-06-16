# PDF 파일 업로드 및 파싱 기능 - 모든 학과 지원

## 개요

경복대학교 물리치료학과, 작업치료학과, 간호학과 교수들이 PDF, Excel 파일을 업로드하면 자동으로 파싱하여 문제 은행에 저장하는 기능입니다.

## 지원 기능

### 🎯 지원 학과
- **물리치료학과**: 근골격계, 신경계, 심폐계, 소아발달, 스포츠의학
- **작업치료학과**: 인지재활, 감각통합, 보조기구, 정신건강, 아동발달  
- **간호학과**: 기본간호, 성인간호, 아동간호, 모성간호, 정신간호, 지역사회간호

### 📄 지원 파일 형식
- PDF (`.pdf`) - Gemini 2.0 Flash로 이미지 분석
- Excel (`.xlsx`, `.xls`) - 구조화된 데이터 파싱
- 텍스트 (`.txt`) - 일반 텍스트 파싱
- Word (`.docx`) - 문서 파싱

### 🤖 AI 분석 기능
- **자동 난이도 분석**: AI가 문제 내용을 분석하여 '하', '중', '상' 난이도 자동 배정
- **학과별 영역 분류**: 각 학과의 전문 영역에 맞게 자동 분류
- **문제 유형 인식**: 객관식, 단답형, 서술형 등 자동 감지
- **실시간 진행률 표시**: 파싱 과정의 모든 단계 실시간 모니터링

## API 엔드포인트

### 1. 파일 업로드
```http
POST /api/professor/upload-questions
Content-Type: multipart/form-data

Form Data:
- file: [파일]
- content_type: "auto" | "questions" | "answers"
- file_title: "파일 제목"
- file_category: "questions"
```

**응답 예시:**
```json
{
  "success": true,
  "message": "작업치료학과 문제 22개 파싱 완료",
  "department": "작업치료학과",
  "total_questions": 22,
  "questions": [
    {
      "id": 1,
      "question_number": 1,
      "content": "인지재활치료에서 주의집중 향상을 위한...",
      "difficulty": "중",
      "area_name": "인지재활"
    }
  ],
  "json_path": "/data/save_parser/20241201_120000_1_작업치료학과_파일.json",
  "supported_areas": ["인지재활", "감각통합", "보조기구", "정신건강", "아동발달"]
}
```

### 2. 실시간 진행률 조회
```http
GET /api/professor/upload-progress/{file_name}
```

**응답 예시:**
```json
{
  "message": "🤖 문제 15 AI 분석 중... (15/22)",
  "progress": 85.5,
  "timestamp": "2024-12-01T12:30:45",
  "user_id": 1,
  "file_name": "exam_questions.pdf",
  "completed": false
}
```

### 3. 승인 대기 문제 조회
```http
GET /api/professor/pending-questions?department_filter=작업치료학과
```

### 4. 학과별 통계
```http
GET /api/professor/department-statistics
```

**응답 예시:**
```json
{
  "department_statistics": {
    "물리치료학과": {
      "total_questions": 66,
      "pending": 22,
      "approved": 44,
      "rejected": 0,
      "difficulty_distribution": {"하": 5, "중": 12, "상": 5},
      "areas": ["근골격계", "신경계", "심폐계"],
      "latest_upload": "2024-12-01T12:00:00"
    },
    "작업치료학과": {
      "total_questions": 44,
      "pending": 22,
      "approved": 22,
      "rejected": 0,
      "difficulty_distribution": {"하": 4, "중": 14, "상": 4},
      "areas": ["인지재활", "감각통합", "보조기구"],
      "latest_upload": "2024-12-01T11:30:00"
    }
  },
  "supported_departments": ["물리치료학과", "작업치료학과", "간호학과"],
  "total_departments": 2,
  "overall_total": 110
}
```

## 사용 시나리오

### 시나리오 1: 물리치료학과 교수 PDF 업로드

1. **파일 업로드**: 물리치료학과 교수가 시험 문제 PDF 업로드
   ```
   📄 파일 분석 중... (2.3 MB)
   🎯 학과 감지 완료: 물리치료학과
   📖 PDF → 이미지 변환 중...
   📄 5개 페이지 이미지 생성 완료
   📖 페이지 1/5 이미지 분석 중...
   📖 페이지 2/5 이미지 분석 중...
   ...
   🤖 AI 문제 분석 시작: 22개 문제
   🤖 문제 1 AI 분석 중... (1/22)
   🤖 문제 2 AI 분석 중... (2/22)
   ...
   ✅ 파싱 완료!
   ```

2. **AI 분석 결과**: 자동으로 물리치료학과 전문 영역 분류
   - 문제 1-5: 근골격계 (난이도: 중)
   - 문제 6-10: 신경계 (난이도: 상)
   - 문제 11-15: 심폐계 (난이도: 하)
   - 문제 16-20: 소아발달 (난이도: 중)
   - 문제 21-22: 스포츠의학 (난이도: 상)

3. **문제 검토**: 교수가 파싱된 문제들을 검토하고 필요시 수정
4. **일괄 승인**: 검토 완료 후 모든 문제 일괄 승인

### 시나리오 2: 작업치료학과 교수 Excel 업로드

1. **Excel 파일 처리**: 구조화된 데이터로 빠른 파싱
   ```
   📊 Excel 파일 로드 중... (작업치료학과)
   🎯 문제 유형 자동 배정 중... (신장훈)
   📊 시트 분석 중: 3개 시트
   📄 시트 '2024년도 문제' 처리 중... (1/3)
   🤖 AI 문제 분석 시작: 22개 문제 (작업치료학과)
   ✅ 파싱 완료!
   ```

2. **학과별 전문 분석**: 작업치료 전문 영역으로 자동 분류
   - 인지재활: 8문제
   - 감각통합: 6문제  
   - 보조기구: 4문제
   - 정신건강: 2문제
   - 아동발달: 2문제

## 주요 특징

### 🎯 자동 학과 감지
- 파일명, 사용자 정보, 내용 키워드로 학과 자동 감지
- 물치, 작치, 간호 등 약어도 인식

### 📊 실시간 진행률
- PDF 이미지 변환 진행률
- 페이지별 분석 진행률  
- AI 분석 문제별 진행률
- 데이터베이스 저장 진행률

### 🤖 AI 기반 분석
- **딥시크 AI**: 문제 내용 기반 난이도 분석
- **Gemini 2.0 Flash**: PDF 이미지 OCR 및 구조 분석
- **평가위원 데이터**: 기존 출제 패턴 학습

### 💾 데이터 지속성
- JSON 파일로 파싱 결과 백업
- 데이터베이스에 메타데이터 저장
- 서버 재시작 후에도 모든 데이터 유지

## 프론트엔드 구현 예시

```javascript
// 파일 업로드
const uploadFile = async (file, department) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('content_type', 'auto');
  formData.append('file_title', file.name);
  
  const response = await fetch('/api/professor/upload-questions', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  
  if (result.success) {
    // 진행률 모니터링 시작
    monitorProgress(file.name);
  }
};

// 진행률 모니터링
const monitorProgress = (fileName) => {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/professor/upload-progress/${fileName}`);
    const progress = await response.json();
    
    updateProgressBar(progress.progress, progress.message);
    
    if (progress.completed) {
      clearInterval(interval);
      loadPendingQuestions(); // 검토 페이지로 이동
    }
  }, 1000); // 1초마다 확인
};
```

## 오류 처리

### 일반적인 오류
- **파일 크기 초과**: 50MB 제한
- **지원되지 않는 형식**: PDF, Excel, 텍스트만 지원
- **파싱 실패**: Gemini API 오류 시 기본값 사용
- **AI 분석 실패**: 위치 기반 난이도 예측 폴백

### 로그 예시
```
⚠️ 문제 15: AI 분석 실패, 위치 기반 예측 사용 (난이도: 중)
❌ 페이지 3 파싱 실패: Invalid JSON response
✅ 문제 검토 페이지 준비 완료: 20개 문제
``` 