<script>
  import { onDestroy } from 'svelte';

  // 마지막 메시지는 검색이 오래 걸릴수록(넓은 키워드일수록) 실제로 가장 오래 떠
  // 있는 메시지입니다 — 카카오맵 확인이 실제로 가장 시간이 오래 걸리는 단계라서,
  // "거의 다 됐다"는 인상을 주는 문구 대신 있는 그대로 설명합니다.
  const progressMessages = [
    '블로그 포스팅을 모으고 있어요',
    'AI가 내용을 분석하고 있어요',
    '결과가 부족하면 지역별로 정리해서 보여드려요',
    '카카오맵에서 실제 있는 곳인지 하나씩 확인하고 있어요'
  ];

  const searchExamples = ['성수동 브런치', '제주 애월 카페', '부산여행'];

  let keyword = '';
  let result = null;
  let overviewResult = null;
  let loading = false;
  let error = '';
  let progressIndex = 0;
  let progressTimer;

  onDestroy(() => clearInterval(progressTimer));

  async function parseResponse(response) {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || '요청을 처리하지 못했습니다.');
    }
    return data;
  }

  async function search() {
    if (!keyword.trim() || loading) return;
    loading = true;
    error = '';
    result = null;
    overviewResult = null;
    progressIndex = 0;
    progressTimer = setInterval(() => {
      progressIndex = Math.min(progressIndex + 1, progressMessages.length - 1);
    }, 4500);

    try {
      const response = await fetch('/api/collections/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword: keyword.trim() })
      });
      const data = await parseResponse(response);
      if (data.mode === 'overview') {
        overviewResult = data;
      } else {
        result = data;
      }
    } catch (requestError) {
      error = requestError.message;
    } finally {
      clearInterval(progressTimer);
      loading = false;
    }
  }

  async function exploreCategory(regionName, categoryName) {
    keyword = `${regionName} ${categoryName}`;
    overviewResult = null;
    error = '';
    loading = true;
    progressIndex = 0;
    progressTimer = setInterval(() => {
      progressIndex = Math.min(progressIndex + 1, progressMessages.length - 1);
    }, 4500);

    try {
      const response = await fetch('/api/collections/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword: keyword.trim() })
      });
      result = await parseResponse(response);
    } catch (requestError) {
      error = requestError.message;
    } finally {
      clearInterval(progressTimer);
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Placepick</title>
</svelte:head>

<header class="site-header">
  <div class="topbar">
    <a class="brand" href="/" aria-label="Placepick 홈">
      <span class="brand-copy"><strong>Placepick</strong><small>blog place curator</small></span>
    </a>
  </div>
</header>

<main class="sheet">
  <section class="hero">
    <p class="hero-kicker">AI BLOG PLACE CURATOR</p>
    <h1 class="hero-sentence">
      <form on:submit|preventDefault={search}>
        <input
          class="keyword-input"
          bind:value={keyword}
          maxlength="80"
          placeholder="성수동 브런치"
          aria-label="네이버 블로그 검색어"
        />
        <button class="submit-arrow" type="submit" disabled={loading || !keyword.trim()} aria-label="장소 찾기">
          {#if loading}
            <span class="spinner" aria-hidden="true"></span>
          {:else}
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>
          {/if}
        </button>
      </form>
      어디가 진짜 좋을까요?
    </h1>

    <div class="hero-examples">
      <span>이렇게 검색해 보세요</span>
      {#each searchExamples as example}
        <button type="button" on:click={() => (keyword = example)}>{example}</button>
      {/each}
    </div>

    <div class="hero-stamp-row">
      <div class="hero-stamp" aria-hidden="true"><b>33</b><span>언급</span></div>
      <p class="hero-stamp-caption">
        별점이 아니라 <strong>언급 횟수</strong>예요. 블로거 여러 명이 같은 곳을
        따로따로 짚었을 때만, 도장을 찍어 확실한 후보로 올려드려요.
      </p>
    </div>
  </section>

  {#if loading}
    <div class="status-line rule" aria-live="polite">
      <span class="caret" aria-hidden="true"></span>
      <span>{progressMessages[progressIndex]}</span>
      <span class="status-note">페이지 수에 따라 1~2분 정도 걸릴 수 있어요. 창을 닫지 말아 주세요.</span>
    </div>
  {/if}

  {#if error}
    <div class="alert" role="alert">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 17h.01"/></svg>
      <div><strong>작업을 완료하지 못했어요</strong><span>{error}</span></div>
      <button type="button" on:click={() => (error = '')} aria-label="닫기">×</button>
    </div>
  {/if}

  {#if overviewResult}
    <section aria-labelledby="overview-results-title">
      <div class="section-heading rule">
        <span class="section-eyebrow">Area Overview</span>
        <h2 id="overview-results-title">이런 지역과 카테고리가 있어요</h2>
        <p>블로그 {overviewResult.post_count}개에서 지역 {overviewResult.regions.length}곳을 찾았어요. 카테고리를 누르면 상세 검색으로 넘어가요.</p>
      </div>

      {#if overviewResult.regions.length === 0}
        <div class="empty-state">
          <span>텅</span>
          <h3>아직 찾은 지역이 없어요</h3>
          <p>검색 범위를 넓히거나 다른 키워드로 다시 찾아보세요.</p>
        </div>
      {:else}
        <div class="region-list">
          {#each overviewResult.regions as region}
            <article class="region-row">
              <div class="region-title-line">
                <h3>{region.name}</h3>
                <span class="region-mentions">블로그 {region.mention_count}회 언급</span>
              </div>
              <div class="category-tabs">
                {#each region.categories as category}
                  <button
                    type="button"
                    class="category-tab"
                    on:click={() => exploreCategory(region.name, category.name)}
                  >
                    {category.name}
                    <span class="tab-count">{category.mention_count}</span>
                  </button>
                {/each}
              </div>
            </article>
          {/each}
        </div>
      {/if}
    </section>
  {/if}

  {#if result}
    <section aria-labelledby="results-title">
      <div class="section-heading rule">
        <span class="section-eyebrow">Your Picks</span>
        <h2 id="results-title">찾은 장소를 확인해 주세요</h2>
        <p>블로그 {result.post_count}개에서 후보 {result.candidates.length}곳을 찾았어요.</p>
      </div>

      {#if result.candidates.length === 0}
        <div class="empty-state">
          <span>텅</span>
          <h3>아직 찾은 장소가 없어요</h3>
          <p>검색 범위를 넓히거나 다른 키워드로 다시 찾아보세요.</p>
        </div>
      {:else}
        <div class="ledger">
          {#each result.candidates as candidate, index}
            <article class:unmatched={!candidate.place} class="ledger-row">
              <span class="row-rank">{String(index + 1).padStart(2, '0')}</span>

              <div class="row-main">
                <div class="row-title-line">
                  <h3>{candidate.place?.display1 || candidate.name}</h3>
                  {#if !candidate.place}<span class="unmatched-badge">매칭 안 됨</span>{/if}
                </div>

                {#if candidate.place}
                  <p class="row-address">
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s6-5.13 6-11a6 6 0 1 0-12 0c0 5.87 6 11 6 11Z"/><circle cx="12" cy="10" r="2"/></svg>
                    {candidate.place.display2}
                  </p>
                  <div class="row-meta">
                    {#if candidate.place.category}<span>{candidate.place.category.split(' > ').at(-1)}</span>{/if}
                    {#if candidate.place.phone}<span>{candidate.place.phone}</span>{/if}
                    {#if candidate.place.business_hours}
                      <span class="hours" class:closed={!candidate.place.business_hours.is_open}>
                        {candidate.place.business_hours.is_open ? '영업중' : '영업종료'} · {candidate.place.business_hours.display}
                      </span>
                    {/if}
                    <span>5km 반경 검색</span>
                  </div>
                {:else}
                  <p class="row-address">카카오맵에서 '{candidate.name}'의 정확한 장소를 찾지 못했어요.</p>
                {/if}

                <div class="row-footer">
                  {#if candidate.sources.length}
                    <details>
                      <summary>증언 {candidate.sources.length}개 보기</summary>
                      <div class="sources">
                        {#each candidate.sources as source}
                          <a href={source.url} target="_blank" rel="noreferrer">
                            <span class="source-badge">N</span>
                            <span class="source-title">{source.title}</span>
                            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 5h5v5M19 5l-8 8"/><path d="M18 13v5H6V6h5"/></svg>
                          </a>
                        {/each}
                      </div>
                    </details>
                  {/if}

                  <div class="link-group">
                    {#if candidate.place?.place_url}
                      <a class="map-link kakao" href={candidate.place.place_url} target="_blank" rel="noreferrer" aria-label={`${candidate.place.display1} 카카오맵에서 보기`}>
                        <span class="dot"></span>카카오맵
                        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>
                      </a>
                    {/if}
                    {#if candidate.naver_search_url}
                      <a class="map-link naver" href={candidate.naver_search_url} target="_blank" rel="noreferrer" aria-label={`${candidate.place?.display1 || candidate.name} 네이버지도에서 보기`}>
                        <span class="dot"></span>네이버지도
                        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>
                      </a>
                    {/if}
                  </div>
                </div>
              </div>

              <span class="row-stamp"><b>{candidate.mention_count}</b><span>언급</span></span>
            </article>
          {/each}
        </div>
      {/if}
    </section>
  {/if}

  {#if !result && !overviewResult && !loading}
    <section>
      <div class="section-heading rule">
        <span class="section-eyebrow">How it works</span>
        <h2>찾고, 확인하고, 골라가세요</h2>
      </div>
      <div class="process-line">
        <article class="process-step">
          <span class="step-num" aria-hidden="true">01</span>
          <h3>블로그 수집</h3>
          <p>검색어와 관련된 네이버 블로그 글을 빠르게 모아요.</p>
        </article>
        <article class="process-step">
          <span class="step-num" aria-hidden="true">02</span>
          <h3>AI 장소 추출</h3>
          <p>글 속 상호명을 구분하고 자주 등장한 순서로 정리해요.</p>
        </article>
        <article class="process-step">
          <span class="step-num" aria-hidden="true">03</span>
          <h3>지도로 이동</h3>
          <p>카카오맵·네이버지도 링크로 바로 이동해 정보를 보고 즐겨찾기하세요.</p>
        </article>
      </div>
    </section>
  {/if}
</main>

<footer class="sheet">
  <a class="brand" href="/">
    <span class="brand-copy"><strong>Placepick</strong></span>
  </a>
  <p>흩어진 취향을 한곳에 모으는 가장 쉬운 방법.</p>
</footer>
