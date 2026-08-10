<script>
  import { onMount } from 'svelte';

  const progressMessages = [
    '블로그 포스팅을 모으고 있어요',
    'AI가 상호명을 구분하고 있어요',
    '카카오맵에서 정확한 장소를 찾고 있어요'
  ];

  let keyword = '';
  let maxPages = 10;
  let topN = 10;
  let radius = 5000;
  let health = null;
  let result = null;
  let loading = false;
  let error = '';
  let progressIndex = 0;
  let progressTimer;

  onMount(async () => {
    try {
      const response = await fetch('/api/health');
      health = await response.json();
    } catch {
      health = { status: 'offline', credentials: {} };
    }
  });

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
    progressIndex = 0;
    progressTimer = setInterval(() => {
      progressIndex = Math.min(progressIndex + 1, progressMessages.length - 1);
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

  function formatDistance(meters) {
    return meters >= 1000 ? `${meters / 1000}km` : `${meters}m`;
  }
</script>

<svelte:head>
  <title>Placepick — 블로그 장소 수집기</title>
</svelte:head>

<header class="topbar">
  <a class="brand" href="/" aria-label="Placepick 홈">
    <span class="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 24 24"><path d="M12 21s6-5.13 6-11a6 6 0 1 0-12 0c0 5.87 6 11 6 11Z"/><circle cx="12" cy="10" r="2.2"/></svg>
    </span>
    <span>Placepick</span>
  </a>

  <div class="status-group">
    <div class:offline={health?.status === 'offline'} class="server-status">
      <span class="status-dot"></span>
      {health === null ? '서버 확인 중' : health.status === 'ok' ? '로컬 서버 연결됨' : '서버 연결 필요'}
    </div>
  </div>
</header>

<main>
  <section class="hero">
    <div class="eyebrow"><span></span> Blog to map, in a few clicks</div>
    <h1>블로그 속 좋은 장소,<br /><em>내 지도에 쏙.</em></h1>
    <p>검색어만 입력하면 자주 언급된 장소를 찾아<br class="desktop-break" /> 카카오맵·네이버지도 링크로 바로 연결해드려요.</p>
  </section>

  <section class="search-panel" aria-labelledby="search-title">
    <div class="panel-heading">
      <div>
        <span class="step-label">STEP 01</span>
        <h2 id="search-title">어떤 장소를 찾아볼까요?</h2>
      </div>
      <span class="privacy-note">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 5 6v5c0 4.8 2.9 8.3 7 10 4.1-1.7 7-5.2 7-10V6l-7-3Z"/><path d="m9 12 2 2 4-4"/></svg>
        모든 작업은 내 컴퓨터에서 실행돼요
      </span>
    </div>

    <form on:submit|preventDefault={search}>
      <label class="keyword-field">
        <span>네이버 블로그 검색어</span>
        <div class="input-wrap">
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m16 16 4 4"/></svg>
          <input bind:value={keyword} maxlength="80" placeholder="" />
          <button type="submit" disabled={loading || !keyword.trim()}>
            {#if loading}
              <span class="spinner"></span> 찾는 중
            {:else}
              장소 찾기
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>
            {/if}
          </button>
        </div>
        <small>지역명과 찾고 싶은 장소 유형을 함께 입력하면 더 정확해요.</small>
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
        <h2>{progressMessages[progressIndex]}</h2>
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

  {#if result}
    <section class="results" aria-labelledby="results-title">
      <div class="results-heading">
        <div>
          <span class="step-label">STEP 03</span>
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
              <div class="rank">{String(index + 1).padStart(2, '0')}</div>
              {#if !candidate.place}<span class="no-match-icon">?</span>{/if}

              <div class="place-content">
                <div class="place-title-row">
                  <h3>{candidate.place?.display1 || candidate.name}</h3>
                  <span class="mentions">{candidate.mention_count}회 언급</span>
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
                    <span>{formatDistance(radius)} 반경 검색</span>
                  </div>
                {:else}
                  <p class="address">카카오맵에서 ‘{candidate.name}’의 정확한 장소를 찾지 못했어요.</p>
                {/if}

                {#if candidate.sources.length}
                  <details>
                    <summary>근거 블로그 {candidate.sources.length}개 보기</summary>
                    <div class="sources">
                      {#each candidate.sources as source}
                        <a href={source.url} target="_blank" rel="noreferrer">
                          <span>N</span>{source.title}
                          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 5h5v5M19 5l-8 8"/><path d="M18 13v5H6V6h5"/></svg>
                        </a>
                      {/each}
                    </div>
                  </details>
                {/if}
              </div>

              <div class="link-group">
                {#if candidate.place?.place_url}
                  <a class="map-link" href={candidate.place.place_url} target="_blank" rel="noreferrer" aria-label={`${candidate.place.display1} 카카오맵에서 보기`}>
                    카카오맵
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>
                  </a>
                {/if}
                {#if candidate.naver_search_url}
                  <a class="map-link" href={candidate.naver_search_url} target="_blank" rel="noreferrer" aria-label={`${candidate.place?.display1 || candidate.name} 네이버지도에서 보기`}>
                    네이버지도
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

  {#if !result && !loading}
    <section class="how-it-works">
      <div class="section-intro">
        <span class="step-label">HOW IT WORKS</span>
        <h2>찾고, 확인하고, 골라가세요</h2>
      </div>
      <div class="process-grid">
        <article>
          <div class="process-icon green">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6"/><path d="m16 16 4 4M8 11h6M11 8v6"/></svg>
          </div>
          <span>01</span><h3>블로그 수집</h3><p>검색어와 관련된 네이버 블로그 글을 빠르게 모아요.</p>
        </article>
        <article>
          <div class="process-icon coral">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 1.7 4.3L18 9l-4.3 1.7L12 15l-1.7-4.3L6 9l4.3-1.7L12 3Z"/><path d="m18 15 .8 2.2L21 18l-2.2.8L18 21l-.8-2.2L15 18l2.2-.8L18 15Z"/></svg>
          </div>
          <span>02</span><h3>AI 장소 추출</h3><p>글 속 상호명을 구분하고 자주 등장한 순서로 정리해요.</p>
        </article>
        <article>
          <div class="process-icon yellow">
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
      <svg viewBox="0 0 24 24"><path d="M12 21s6-5.13 6-11a6 6 0 1 0-12 0c0 5.87 6 11 6 11Z"/><circle cx="12" cy="10" r="2.2"/></svg>
    </span>
    <span>Placepick</span>
  </a>
  <p>흩어진 취향을 한곳에 모으는 가장 쉬운 방법.</p>
</footer>
