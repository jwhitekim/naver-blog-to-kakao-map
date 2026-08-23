<script>
  import { onDestroy } from 'svelte';
  import { get } from 'svelte/store';
  import { lang, t, setLang } from './i18n.js';

  // 검색 예시는 실제 한국어 검색어라 번역하지 않는다(번역하면 검색이 안 됨).
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
      throw new Error(data.detail || get(t).errorGeneric);
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
      progressIndex = Math.min(progressIndex + 1, $t.progress.length - 1);
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
      progressIndex = Math.min(progressIndex + 1, $t.progress.length - 1);
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
    <a class="brand" href="/" aria-label={$t.brandHomeAria}>
      <span class="brand-copy"><strong>Placepick</strong><small>{$t.brandTagline}</small></span>
    </a>
    <div class="lang-toggle" role="group" aria-label={$t.langLabel}>
      <button type="button" class:active={$lang === 'ko'} aria-pressed={$lang === 'ko'} on:click={() => setLang('ko')}>KO</button>
      <span aria-hidden="true">/</span>
      <button type="button" class:active={$lang === 'en'} aria-pressed={$lang === 'en'} on:click={() => setLang('en')}>EN</button>
    </div>
  </div>
</header>

<main class="sheet">
  <section class="hero">
    <p class="hero-kicker">{$t.heroKicker}</p>
    <h1 class="hero-sentence">
      <form on:submit|preventDefault={search}>
        <input
          class="keyword-input"
          bind:value={keyword}
          maxlength="80"
          placeholder="성수동 브런치"
          aria-label={$t.keywordAria}
        />
        <button class="submit-arrow" type="submit" disabled={loading || !keyword.trim()} aria-label={$t.submitAria}>
          {#if loading}
            <span class="spinner" aria-hidden="true"></span>
          {:else}
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>
          {/if}
        </button>
      </form>
      <span class="hero-sentence-tail">{$t.heroTail}</span>
    </h1>

    <div class="hero-examples">
      <span>{$t.examplesLabel}</span>
      {#each searchExamples as example}
        <button type="button" on:click={() => (keyword = example)}>{example}</button>
      {/each}
    </div>

    <div class="hero-stamp-row">
      <div class="hero-stamp" aria-hidden="true"><b>33</b><span>{$t.stampLabel}</span></div>
      <p class="hero-stamp-caption">{@html $t.heroCaption}</p>
    </div>
  </section>

  {#if loading}
    <div class="status-line rule" aria-live="polite">
      <span class="caret" aria-hidden="true"></span>
      <span>{$t.progress[progressIndex]}</span>
      <span class="status-note">{$t.statusNote}</span>
    </div>
  {/if}

  {#if error}
    <div class="alert" role="alert">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 17h.01"/></svg>
      <div><strong>{$t.alertTitle}</strong><span>{error}</span></div>
      <button type="button" on:click={() => (error = '')} aria-label={$t.alertClose}>×</button>
    </div>
  {/if}

  {#if overviewResult}
    <section aria-labelledby="overview-results-title">
      <div class="section-heading rule">
        <span class="section-eyebrow">Area Overview</span>
        <h2 id="overview-results-title">{$t.overviewTitle}</h2>
        <p>{$t.overviewSummary(overviewResult.post_count, overviewResult.regions.length)}</p>
      </div>

      {#if overviewResult.regions.length === 0}
        <div class="empty-state">
          <span>{$t.emptyGlyph}</span>
          <h3>{$t.overviewEmptyTitle}</h3>
          <p>{$t.emptyDesc}</p>
        </div>
      {:else}
        <div class="region-list">
          {#each overviewResult.regions as region}
            <article class="region-row">
              <div class="region-title-line">
                <h3>{region.name}</h3>
                <span class="region-mentions">{$t.regionMentions(region.mention_count)}</span>
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
        <h2 id="results-title">{$t.picksTitle}</h2>
        <p>{$t.picksSummary(result.post_count, result.candidates.length)}</p>
      </div>

      {#if result.candidates.length === 0}
        <div class="empty-state">
          <span>{$t.emptyGlyph}</span>
          <h3>{$t.picksEmptyTitle}</h3>
          <p>{$t.emptyDesc}</p>
        </div>
      {:else}
        <div class="ledger">
          {#each result.candidates as candidate, index}
            <article class:unmatched={!candidate.place} class="ledger-row">
              <span class="row-rank">{String(index + 1).padStart(2, '0')}</span>

              <div class="row-main">
                <div class="row-title-line">
                  <h3>{candidate.place?.display1 || candidate.name}</h3>
                  {#if !candidate.place}<span class="unmatched-badge">{$t.unmatchedBadge}</span>{/if}
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
                        {candidate.place.business_hours.is_open ? $t.open : $t.closed} · {candidate.place.business_hours.display}
                      </span>
                    {/if}
                    <span>{$t.radiusMeta}</span>
                  </div>
                {:else}
                  <p class="row-address">{$t.unmatchedAddress(candidate.name)}</p>
                {/if}

                <div class="row-footer">
                  {#if candidate.sources.length}
                    <details>
                      <summary>{$t.sourcesSummary(candidate.sources.length)}</summary>
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
                      <a class="map-link kakao" href={candidate.place.place_url} target="_blank" rel="noreferrer" aria-label={$t.kakaoAria(candidate.place.display1)}>
                        <span class="dot"></span>{$t.kakaoLink}
                        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>
                      </a>
                    {/if}
                    {#if candidate.naver_search_url}
                      <a class="map-link naver" href={candidate.naver_search_url} target="_blank" rel="noreferrer" aria-label={$t.naverAria(candidate.place?.display1 || candidate.name)}>
                        <span class="dot"></span>{$t.naverLink}
                        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>
                      </a>
                    {/if}
                  </div>
                </div>
              </div>

              <span class="row-stamp"><b>{candidate.mention_count}</b><span>{$t.stampLabel}</span></span>
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
        <h2>{$t.howTitle}</h2>
      </div>
      <div class="process-line">
        <article class="process-step">
          <span class="step-num" aria-hidden="true">01</span>
          <h3>{$t.step1Title}</h3>
          <p>{$t.step1Desc}</p>
        </article>
        <article class="process-step">
          <span class="step-num" aria-hidden="true">02</span>
          <h3>{$t.step2Title}</h3>
          <p>{$t.step2Desc}</p>
        </article>
        <article class="process-step">
          <span class="step-num" aria-hidden="true">03</span>
          <h3>{$t.step3Title}</h3>
          <p>{$t.step3Desc}</p>
        </article>
      </div>
    </section>
  {/if}
</main>

<footer class="sheet">
  <a class="brand" href="/">
    <span class="brand-copy"><strong>Placepick</strong></span>
  </a>
  <p>{$t.footerTagline}</p>
</footer>
