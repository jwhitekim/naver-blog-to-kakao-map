import { writable, derived } from 'svelte/store';

// UI 문구만 담는다. 검색 결과 데이터(상호명·주소·카테고리·영업시간 display·
// 블로그 제목 등 API 응답 값)는 절대 여기 넣지 않는다 — 실제 한국어 데이터라
// 번역하면 사용자가 그 장소를 못 찾게 된다.

const STORAGE_KEY = 'placepick-lang';

function readInitial() {
  if (typeof localStorage === 'undefined') return 'ko';
  const saved = localStorage.getItem(STORAGE_KEY);
  return saved === 'en' || saved === 'ko' ? saved : 'ko';
}

export const lang = writable(readInitial());

lang.subscribe((value) => {
  if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY, value);
  if (typeof document !== 'undefined') document.documentElement.lang = value;
});

export function setLang(value) {
  if (value === 'ko' || value === 'en') lang.set(value);
}

const dict = {
  ko: {
    brandHomeAria: 'Placepick 홈',
    brandTagline: 'blog place curator',
    langLabel: '언어 선택',

    heroKicker: 'AI BLOG PLACE CURATOR',
    heroTail: '어디가 진짜 좋을까요?',
    keywordAria: '네이버 블로그 검색어',
    submitAria: '장소 찾기',
    examplesLabel: '이렇게 검색해 보세요',
    stampLabel: '언급',
    heroCaption:
      '별점이 아니라 <strong>언급 횟수</strong>예요. 블로거 여러 명이 같은 곳을 따로따로 짚었을 때만, 도장을 찍어 확실한 후보로 올려드려요.',

    statusNote: '페이지 수에 따라 1~2분 정도 걸릴 수 있어요. 창을 닫지 말아 주세요.',
    progress: [
      '블로그 포스팅을 모으고 있어요',
      'AI가 내용을 분석하고 있어요',
      '결과가 부족하면 지역별로 정리해서 보여드려요',
      '카카오맵에서 실제 있는 곳인지 하나씩 확인하고 있어요'
    ],

    alertTitle: '작업을 완료하지 못했어요',
    alertClose: '닫기',
    errorGeneric: '요청을 처리하지 못했습니다.',

    overviewTitle: '이런 지역과 카테고리가 있어요',
    overviewSummary: (posts, regions) =>
      `블로그 ${posts}개에서 지역 ${regions}곳을 찾았어요. 카테고리를 누르면 상세 검색으로 넘어가요.`,
    overviewEmptyTitle: '아직 찾은 지역이 없어요',
    regionMentions: (n) => `블로그 ${n}회 언급`,

    picksTitle: '찾은 장소를 확인해 주세요',
    picksSummary: (posts, candidates) => `블로그 ${posts}개에서 후보 ${candidates}곳을 찾았어요.`,
    picksEmptyTitle: '아직 찾은 장소가 없어요',

    emptyGlyph: '텅',
    emptyDesc: '검색 범위를 넓히거나 다른 키워드로 다시 찾아보세요.',

    unmatchedBadge: '매칭 안 됨',
    open: '영업중',
    closed: '영업종료',
    radiusMeta: '5km 반경 검색',
    unmatchedAddress: (name) => `카카오맵에서 '${name}'의 정확한 장소를 찾지 못했어요.`,
    sourcesSummary: (n) => `증언 ${n}개 보기`,
    kakaoLink: '카카오맵',
    naverLink: '네이버지도',
    kakaoAria: (name) => `${name} 카카오맵에서 보기`,
    naverAria: (name) => `${name} 네이버지도에서 보기`,

    howTitle: '찾고, 확인하고, 골라가세요',
    step1Title: '블로그 수집',
    step1Desc: '검색어와 관련된 네이버 블로그 글을 빠르게 모아요.',
    step2Title: 'AI 장소 추출',
    step2Desc: '글 속 상호명을 구분하고 자주 등장한 순서로 정리해요.',
    step3Title: '지도로 이동',
    step3Desc: '카카오맵·네이버지도 링크로 바로 이동해 정보를 보고 즐겨찾기하세요.',

    footerTagline: '흩어진 취향을 한곳에 모으는 가장 쉬운 방법.'
  },

  en: {
    brandHomeAria: 'Placepick home',
    brandTagline: 'blog place curator',
    langLabel: 'Language',

    heroKicker: 'AI BLOG PLACE CURATOR',
    heroTail: 'so where is actually good?',
    keywordAria: 'Naver blog search keyword',
    submitAria: 'Find places',
    examplesLabel: 'Try searching like this',
    stampLabel: 'mentions',
    heroCaption:
      "It's not a star rating — it's the <strong>number of mentions</strong>. Only when several bloggers point to the same place on their own do we stamp it as a solid pick.",

    statusNote: 'This can take 1–2 minutes depending on how many posts there are. Please keep this window open.',
    progress: [
      'Gathering blog posts',
      'AI is reading through the content',
      "If there aren't enough results, we'll group them by area",
      'Checking each place against KakaoMap to confirm it really exists'
    ],

    alertTitle: "We couldn't finish that",
    alertClose: 'Close',
    errorGeneric: "We couldn't process your request.",

    overviewTitle: 'Here are the areas and categories',
    overviewSummary: (posts, regions) =>
      `We found ${regions} area${regions === 1 ? '' : 's'} across ${posts} blog post${posts === 1 ? '' : 's'}. Tap a category to run a detailed search.`,
    overviewEmptyTitle: 'No areas found yet',
    regionMentions: (n) => `${n} blog mention${n === 1 ? '' : 's'}`,

    picksTitle: 'Here are your picks',
    picksSummary: (posts, candidates) =>
      `We found ${candidates} spot${candidates === 1 ? '' : 's'} across ${posts} blog post${posts === 1 ? '' : 's'}.`,
    picksEmptyTitle: 'No places found yet',

    emptyGlyph: 'Empty',
    emptyDesc: 'Try a broader search or a different keyword.',

    unmatchedBadge: 'No match',
    open: 'Open',
    closed: 'Closed',
    radiusMeta: '5 km radius',
    unmatchedAddress: (name) => `We couldn't pinpoint '${name}' on KakaoMap.`,
    sourcesSummary: (n) => `See ${n} source${n === 1 ? '' : 's'}`,
    kakaoLink: 'KakaoMap',
    naverLink: 'Naver Map',
    kakaoAria: (name) => `View ${name} on KakaoMap`,
    naverAria: (name) => `View ${name} on Naver Map`,

    howTitle: 'Find, verify, pick',
    step1Title: 'Collect blogs',
    step1Desc: 'We quickly gather Naver blog posts related to your search.',
    step2Title: 'AI extracts places',
    step2Desc: 'It sorts out the business names and ranks them by how often they appear.',
    step3Title: 'Jump to the map',
    step3Desc: 'Open KakaoMap or Naver Map links to check the details and save favorites.',

    footerTagline: 'The easiest way to gather scattered tastes in one place.'
  }
};

export const t = derived(lang, ($lang) => dict[$lang]);
