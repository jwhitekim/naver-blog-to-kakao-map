<script>
  import { onDestroy } from 'svelte';

  const progressMessages = [
    '블로그 포스팅을 모으고 있어요',
    'AI가 상호명을 구분하고 있어요',
    '카카오맵에서 정확한 장소를 찾고 있어요'
  ];

  const overviewProgressMessages = [
    '블로그 포스팅을 모으고 있어요',
    'AI가 지역과 카테고리를 정리하고 있어요'
  ];

  const searchExamples = ['성수동 브런치', '제주 애월 카페', '부산 해운대 맛집'];

  let mode = 'quick'; // 'quick' | 'overview'
  let keyword = '';
  let maxPages = 10;
  let topN = 10;
  let radius = 5000;
  let result = null;
  let overviewResult = null;
  let loading = false;
  let error = '';
  let progressIndex = 0;
  let progressTimer;

  $: currentProgressMessages = mode === 'overview' ? overviewProgressMessages : progressMessages;

  onDestroy(() => clearInterval(progressTimer));

  async function parseResponse(response) {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || '요청을 처리하지 못했습니다.');
    }
    return data;
  }

  function handleSubmit() {
    return mode === 'overview' ? searchOverview() : search();
  }

  async function search() {
    if (!keyword.trim() || loading) return;
    loading = true;
    error = '';
    result = null;
    overviewResult = null;
    progressIndex = 0;
    progressTimer = setInterval(() => {
      progressIndex = Math.min(progressIndex + 1, currentProgressMessages.length - 1);
    }, 4500);

    try {
      const response = await fetch('/api/collections/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keyword: keyword.trim(),
          max_pages: Number(maxPages),
          top_n: Number(topN),
          radius: Number(radius)
        })
      });
      result = await parseResponse(response);
    } catch (requestError) {
      error = requestError.message;
    } finally {
      clearInterval(progressTimer);
      loading = false;
    }
  }

  async function searchOverview() {
    if (!keyword.trim() || loading) return;
    loading = true;
    error = '';
    overviewResult = null;
    result = null;
    progressIndex = 0;
    progressTimer = setInterval(() => {
      progressIndex = Math.min(progressIndex + 1, currentProgressMessages.length - 1);
    }, 4500);

    try {
      const response = await fetch('/api/collections/overview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keyword: keyword.trim(),
          max_pages: Number(maxPages)
        })
      });
      overviewResult = await parseResponse(response);
    } catch (requestError) {
      error = requestError.message;
    } finally {
      clearInterval(progressTimer);
      loading = false;
    }
  }

  function exploreCategory(regionName, categoryName) {
    keyword = `${regionName} ${categoryName}`;
    mode = 'quick';
    overviewResult = null;
    search();
  }

  function formatDistance(meters) {
    return meters >= 1000 ? `${meters / 1000}km` : `${meters}m`;
  }
</script>

<svelte:head>
  <title>Placepick</title>
</svelte:head>

<header class="site-header">
  <div class="topbar">
    <a class="brand" href="/" aria-label="Placepick 홈">
      <span class="brand-mark" aria-hidden="true">
        <img src="/apple-touch-icon.png" alt="" />
      </span>
      <span class="brand-copy"><strong>Placepick</strong><small>blog place curator</small></span>
    </a>

  </div>
</header>

<main>
  <section class="hero">
    <div class="hero-copy">
      <div class="eyebrow">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 1.7 4.3L18 9l-4.3 1.7L12 15l-1.7-4.3L6 9l4.3-1.7L12 3Z"/></svg>
        AI blog place curator
      </div>
      <h1>검색은 짧게,<br />장소 발견은 <em>깊게.</em></h1>
      <p>수많은 블로그 후기를 한 번에 읽고, 자주 언급된 장소만 골라 지도 링크로 정리해드려요.</p>
      <div class="hero-points" aria-label="서비스 특징">
        <span><i></i> 실제 블로그 언급 기반</span>
        <span><i></i> 카카오·네이버 지도 연결</span>
      </div>
    </div>

    <div class="hero-visual" aria-hidden="true">
      <div class="map-canvas">
        <svg class="map-lines" viewBox="0 0 480 360" preserveAspectRatio="none">
          <path d="M-20 89C73 43 132 112 211 80s112-9 160-55 94-18 137 5" />
          <path d="M82-20c-6 89 51 108 32 174s-1 130 90 226" />
          <path d="M-30 284c98-67 139 10 235-37s147-31 306 38" />
          <path d="M337-20c-30 79 36 120 6 187s15 129 78 213" />
        </svg>
        <div class="map-label label-seongsu">성수동</div>
        <div class="map-label label-seoulforest">서울숲</div>
        <div class="map-label label-tukseom">뚝섬</div>

        <span class="map-pin pin-one"><b>1</b></span>
        <span class="map-pin pin-two"><b>2</b></span>
        <span class="map-pin pin-three"><b>3</b></span>

        <div class="floating-place place-one">
          <span class="place-thumbnail">☕</span>
          <span><small>블로그 12회 언급</small><strong>어니언 성수</strong></span>
          <b>01</b>
        </div>
        <div class="floating-place place-two">
          <span class="place-thumbnail lavender">🥐</span>
          <span><small>블로그 8회 언급</small><strong>브레디포스트</strong></span>
          <b>02</b>
        </div>

        <div class="map-summary">
          <span class="summary-icon"><svg viewBox="0 0 24 24"><path d="m12 3 1.7 4.3L18 9l-4.3 1.7L12 15l-1.7-4.3L6 9l4.3-1.7L12 3Z"/></svg></span>
          <span><strong>취향 장소 10곳</strong><small>AI가 발견했어요</small></span>
        </div>
      </div>
    </div>
  </section>

  <section class="search-panel" aria-labelledby="search-title">
    <div class="panel-heading">
      <div>
        <span class="step-label"><i>01</i> START PICKING</span>
        <h2 id="search-title">어떤 장소를 찾아볼까요?</h2>
        <p class="panel-description">지역과 원하는 장소를 함께 입력해 주세요.</p>
      </div>
      <span class="privacy-note">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s6-5.13 6-11a6 6 0 1 0-12 0c0 5.87 6 11 6 11Z"/><circle cx="12" cy="10" r="2"/></svg>
        찾은 장소는 지도에서 바로 확인해요
      </span>
    </div>

    <div class="mode-tabs" role="tablist" aria-label="검색 모드">
      <button type="button" role="tab" aria-selected={mode === 'quick'} class:active={mode === 'quick'} on:click={() => (mode = 'quick')}>빠른 검색</button>
      <button type="button" role="tab" aria-selected={mode === 'overview'} class:active={mode === 'overview'} on:click={() => (mode = 'overview')}>여행지 개요</button>
    </div>

    <form on:submit|preventDefault={handleSubmit}>
      <label class="keyword-field">
        <span>네이버 블로그 검색어</span>
        <div class="input-wrap">
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m16 16 4 4"/></svg>
          <input
            bind:value={keyword}
            maxlength="80"
            placeholder={mode === 'overview' ? '예: 부산여행, 제주도 3박4일' : '예: 성수동 브런치 맛집'}
            aria-label="네이버 블로그 검색어"
          />
          <button type="submit" disabled={loading || !keyword.trim()}>
            {#if loading}
              <span class="spinner"></span> 찾는 중
            {:else}
              {mode === 'overview' ? '개요 찾기' : '장소 찾기'}
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>
            {/if}
          </button>
        </div>
        <div class="search-examples">
          <small>이렇게 검색해 보세요</small>
          {#each searchExamples as example}
            <button type="button" on:click={() => (keyword = example)}>{example}</button>
          {/each}
        </div>
      </label>

      <div class="options-grid">
        <label>
          <span>수집 페이지</span>
          <div class="select-wrap">
            <select bind:value={maxPages}>
              <option value={5}>5페이지 · 빠르게</option>
              <option value={10}>10페이지 · 권장</option>
              <option value={20}>20페이지 · 꼼꼼하게</option>
              <option value={30}>30페이지 · 최대</option>
            </select>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8 10 4 4 4-4"/></svg>
          </div>
        </label>
        {#if mode === 'quick'}
          <label>
            <span>가져올 장소</span>
            <div class="select-wrap">
              <select bind:value={topN}>
                <option value={5}>상위 5곳</option>
                <option value={10}>상위 10곳</option>
                <option value={15}>상위 15곳</option>
                <option value={20}>상위 20곳</option>
              </select>
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8 10 4 4 4-4"/></svg>
            </div>
          </label>
          <label>
            <span>검색 반경</span>
            <div class="select-wrap">
              <select bind:value={radius}>
                <option value={1000}>1km</option>
                <option value={3000}>3km</option>
                <option value={5000}>5km · 권장</option>
                <option value={10000}>10km</option>
                <option value={20000}>20km</option>
              </select>
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8 10 4 4 4-4"/></svg>
            </div>
          </label>
        {/if}
      </div>
    </form>
  </section>

  {#if loading}
    <section class="loading-card" aria-live="polite">
      <div class="radar">
        <span></span>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s6-5.13 6-11a6 6 0 1 0-12 0c0 5.87 6 11 6 11Z"/><circle cx="12" cy="10" r="2"/></svg>
      </div>
      <div>
        <span class="step-label">STEP 02</span>
        <h2>{currentProgressMessages[progressIndex]}</h2>
        <p>페이지 수에 따라 1~2분 정도 걸릴 수 있어요. 창을 닫지 말아 주세요.</p>
        <div class="progress-track"><span style={`width: ${(progressIndex + 1) * 32}%`}></span></div>
      </div>
    </section>
  {/if}

  {#if error}
    <div class="alert error-alert" role="alert">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 17h.01"/></svg>
      <div><strong>작업을 완료하지 못했어요</strong><span>{error}</span></div>
      <button type="button" on:click={() => (error = '')} aria-label="닫기">×</button>
    </div>
  {/if}

  {#if overviewResult}
    <section class="results" aria-labelledby="overview-results-title">
      <div class="results-heading">
        <div>
          <span class="step-label"><i>03</i> AREA OVERVIEW</span>
          <h2 id="overview-results-title">이런 지역과 카테고리가 있어요</h2>
          <p>블로그 {overviewResult.post_count}개에서 지역 {overviewResult.regions.length}곳을 찾았어요. 카테고리를 클릭하면 상세 검색으로 넘어가요.</p>
        </div>
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
            <article class="region-card">
              <div class="region-title-row">
                <h3>{region.name}</h3>
                <span class="mentions">블로그 {region.mention_count}회 언급</span>
              </div>
              <div class="category-chips">
                {#each region.categories as category}
                  <button
                    type="button"
                    class="category-chip"
                    on:click={() => exploreCategory(region.name, category.name)}
                  >
                    {category.name}
                    <span class="chip-count">{category.mention_count}</span>
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
    <section class="results" aria-labelledby="results-title">
      <div class="results-heading">
        <div>
          <span class="step-label"><i>03</i> YOUR PICKS</span>
          <h2 id="results-title">찾은 장소를 확인해 주세요</h2>
          <p>블로그 {result.post_count}개에서 후보 {result.candidates.length}곳을 찾았어요.</p>
        </div>
      </div>

      {#if result.candidates.length === 0}
        <div class="empty-state">
          <span>텅</span>
          <h3>아직 찾은 장소가 없어요</h3>
          <p>검색 범위를 넓히거나 다른 키워드로 다시 찾아보세요.</p>
        </div>
      {:else}
        <div class="place-list">
          {#each result.candidates as candidate, index}
            <article class:unmatched={!candidate.place} class="place-card">
              <div class="place-avatar" class:no-match={!candidate.place}>
                {#if candidate.place}
                  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s6-5.13 6-11a6 6 0 1 0-12 0c0 5.87 6 11 6 11Z"/><circle cx="12" cy="10" r="2.2"/></svg>
                {:else}
                  <span>?</span>
                {/if}
              </div>

              <div class="place-content">
                <div class="place-title-row">
                  <span class="rank">{String(index + 1).padStart(2, '0')}</span>
                  <h3>{candidate.place?.display1 || candidate.name}</h3>
                  {#if !candidate.place}<span class="unmatched-badge">매칭 안 됨</span>{/if}
                </div>

                {#if candidate.place}
                  <p class="address">
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s6-5.13 6-11a6 6 0 1 0-12 0c0 5.87 6 11 6 11Z"/><circle cx="12" cy="10" r="2"/></svg>
                    {candidate.place.display2}
                  </p>
                  <div class="meta">
                    {#if candidate.place.category}<span>{candidate.place.category.split(' > ').at(-1)}</span>{/if}
                    {#if candidate.place.phone}<span>{candidate.place.phone}</span>{/if}
                    {#if candidate.place.business_hours}
                      <span class="hours" class:closed={!candidate.place.business_hours.is_open}>
                        {candidate.place.business_hours.is_open ? '영업중' : '영업종료'} · {candidate.place.business_hours.display}
                      </span>
                    {/if}
                    <span>{formatDistance(radius)} 반경 검색</span>
                  </div>
                {:else}
                  <p class="address">카카오맵에서 ‘{candidate.name}’의 정확한 장소를 찾지 못했어요.</p>
                {/if}

                <div class="card-footer">
                  <span class="mentions">블로그 {candidate.mention_count}회 언급</span>

                  {#if candidate.sources.length}
                    <details>
                      <summary>근거 {candidate.sources.length}개 보기</summary>
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
                </div>
              </div>

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
            </article>
          {/each}
        </div>
      {/if}
    </section>
  {/if}

  {#if !result && !overviewResult && !loading}
    <section class="how-it-works">
      <div class="section-intro">
        <span class="step-label">HOW IT WORKS</span>
        <h2>찾고, 확인하고, 골라가세요</h2>
      </div>
      <div class="process-grid">
        <article>
          <div class="process-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6"/><path d="m16 16 4 4M8 11h6M11 8v6"/></svg>
          </div>
          <span>01</span><h3>블로그 수집</h3><p>검색어와 관련된 네이버 블로그 글을 빠르게 모아요.</p>
        </article>
        <article>
          <div class="process-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 1.7 4.3L18 9l-4.3 1.7L12 15l-1.7-4.3L6 9l4.3-1.7L12 3Z"/><path d="m18 15 .8 2.2L21 18l-2.2.8L18 21l-.8-2.2L15 18l2.2-.8L18 15Z"/></svg>
          </div>
          <span>02</span><h3>AI 장소 추출</h3><p>글 속 상호명을 구분하고 자주 등장한 순서로 정리해요.</p>
        </article>
        <article>
          <div class="process-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s6-5.13 6-11a6 6 0 1 0-12 0c0 5.87 6 11 6 11Z"/><circle cx="12" cy="10" r="2"/></svg>
          </div>
          <span>03</span><h3>지도로 이동</h3><p>카카오맵·네이버지도 링크로 바로 이동해 정보를 보고 즐겨찾기하세요.</p>
        </article>
      </div>
    </section>
  {/if}
</main>

<footer>
  <a class="brand footer-brand" href="/">
    <span class="brand-mark" aria-hidden="true">
      <img src="/apple-touch-icon.png" alt="" />
    </span>
    <span>Placepick</span>
  </a>
  <p>흩어진 취향을 한곳에 모으는 가장 쉬운 방법.</p>
</footer>
