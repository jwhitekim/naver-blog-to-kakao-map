<script>
  import { onDestroy, onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { lang, t, setLang } from './i18n.js';

  // 검색 예시는 실제 한국어 검색어라 번역하지 않는다(번역하면 검색이 안 됨).
  const searchExamples = ['성수동 브런치', '제주 애월 카페', '부산여행'];
  const samplePicks = [
    { rank: '01', name: '버티샌드위치하우스 성수점', area: '서울 성동구', category: '샌드위치', mentions: 12, sources: 4 },
    { rank: '02', name: '성수다락', area: '서울 성동구', category: '양식', mentions: 7, sources: 3 },
    { rank: '03', name: '서울앵무새', area: '서울 성동구', category: '카페', mentions: 5, sources: 2 }
  ];

  function routeFromLocation() {
    return window.location.pathname.replace(/\/+$/, '') === '/search' ? 'search' : 'home';
  }

  let route = typeof window === 'undefined' ? 'home' : routeFromLocation();

  let keyword = '';
  let result = null;
  let overviewResult = null;
  let loading = false;
  let error = '';
  let progressIndex = 0;
  let progressTimer;

  onMount(() => {
    const handlePopState = () => {
      route = routeFromLocation();
      window.scrollTo({ top: 0, behavior: 'auto' });
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  });

  onDestroy(() => clearInterval(progressTimer));

  function navigate(event, path) {
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) return;

    event.preventDefault();
    if (window.location.pathname !== path) window.history.pushState({}, '', path);
    route = path === '/search' ? 'search' : 'home';
    window.scrollTo({ top: 0, behavior: 'auto' });
  }

  function scrollReveal(node, options = {}) {
    const { delay = 0, distance = 28 } = options;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    node.classList.add('scroll-reveal');
    node.style.setProperty('--reveal-delay', `${delay}ms`);
    node.style.setProperty('--reveal-offset', `${distance}px`);

    if (reduceMotion.matches || !('IntersectionObserver' in window)) {
      node.classList.add('is-visible');
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && entry.intersectionRatio >= 0.16) {
          node.classList.add('is-visible');
          return;
        }

        if (!entry.isIntersecting) {
          const rootTop = entry.rootBounds?.top ?? 0;
          const rootBottom = entry.rootBounds?.bottom ?? window.innerHeight;
          const exitedAbove = entry.boundingClientRect.bottom <= rootTop;
          const exitedBelow = entry.boundingClientRect.top >= rootBottom;

          if (exitedAbove || exitedBelow) {
            node.style.setProperty(
              '--reveal-offset',
              `${exitedAbove ? -distance : distance}px`
            );
            node.classList.remove('is-visible');
          }
        }
      },
      { threshold: [0, 0.16] }
    );

    observer.observe(node);

    return {
      destroy() {
        observer.disconnect();
      }
    };
  }

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
  <title>{route === 'home' ? 'Placepick' : `Placepick — ${$t.submitAria}`}</title>
</svelte:head>

<header class="site-header">
  <div class="topbar">
    <a class="brand" href="/" aria-label={$t.brandHomeAria} on:click={(event) => navigate(event, '/')}>
      <span class="brand-copy"><strong>Placepick</strong><small>{$t.brandTagline}</small></span>
    </a>
    <div class="header-actions">
      {#if route === 'home'}
        <a class="header-nav-link" href="/search" on:click={(event) => navigate(event, '/search')}>{$t.headerUse}</a>
      {:else}
        <a class="header-nav-link" href="/" on:click={(event) => navigate(event, '/')}>{$t.headerAbout}</a>
      {/if}
      <div class="lang-toggle" role="group" aria-label={$t.langLabel}>
        <button type="button" class:active={$lang === 'ko'} aria-pressed={$lang === 'ko'} on:click={() => setLang('ko')}>KO</button>
        <span aria-hidden="true">/</span>
        <button type="button" class:active={$lang === 'en'} aria-pressed={$lang === 'en'} on:click={() => setLang('en')}>EN</button>
      </div>
    </div>
  </div>
</header>

{#if route === 'home'}
  <main class="sheet home-page">
    <section class="landing-hero">
      <div class="landing-hero-copy">
        <p class="hero-kicker" use:scrollReveal>{$t.homeHeroKicker}</p>
        <h1 use:scrollReveal={{ delay: 70 }}>{@html $t.homeHeroTitle}</h1>
        <p class="landing-lead" use:scrollReveal={{ delay: 140 }}>{$t.homeHeroDesc}</p>
        <a class="primary-cta" href="/search" on:click={(event) => navigate(event, '/search')} use:scrollReveal={{ delay: 210 }}>
          <span>{$t.homePrimaryCta}</span>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>
        </a>
      </div>
      <div class="landing-proof" use:scrollReveal={{ delay: 170 }}>
        <span class="proof-label">{$t.homeProofLabel}</span>
        <div class="landing-stamp" aria-hidden="true"><b>12</b><span>{$t.stampLabel}</span></div>
        <p>{$t.homeProofCaption}</p>
      </div>
    </section>

    <section id="how-it-works" class="home-section">
      <div class="section-heading rule" use:scrollReveal>
        <span class="section-eyebrow">{$t.homeProcessEyebrow}</span>
        <h2>{$t.homeProcessTitle}</h2>
        <p>{$t.homeProcessDesc}</p>
      </div>
      <div class="home-process-line">
        <article class="home-process-step" use:scrollReveal>
          <span class="step-num" aria-hidden="true">01</span>
          <h3>{$t.homeStep1Title}</h3><p>{$t.homeStep1Desc}</p>
        </article>
        <article class="home-process-step" use:scrollReveal={{ delay: 80 }}>
          <span class="step-num" aria-hidden="true">02</span>
          <h3>{$t.homeStep2Title}</h3><p>{$t.homeStep2Desc}</p>
        </article>
        <article class="home-process-step" use:scrollReveal={{ delay: 160 }}>
          <span class="step-num" aria-hidden="true">03</span>
          <h3>{$t.homeStep3Title}</h3><p>{$t.homeStep3Desc}</p>
        </article>
        <article class="home-process-step" use:scrollReveal={{ delay: 240 }}>
          <span class="step-num" aria-hidden="true">04</span>
          <h3>{$t.homeStep4Title}</h3><p>{$t.homeStep4Desc}</p>
        </article>
      </div>
    </section>

    <section class="home-section home-example">
      <div class="section-heading rule" use:scrollReveal>
        <span class="section-eyebrow">{$t.homeExampleEyebrow}</span>
        <h2>{$t.homeExampleTitle}</h2>
        <p>{$t.homeExampleDesc}</p>
      </div>
      <div class="sample-query" use:scrollReveal>{$t.homeExampleQuery}</div>
      <div class="sample-ledger">
        {#each samplePicks as pick, index}
          <article class="sample-row" use:scrollReveal={{ delay: index * 80 }}>
            <span class="sample-rank">{pick.rank}</span>
            <div class="sample-main">
              <h3>{pick.name}</h3>
              <p>{pick.area} · {pick.category}</p>
              <span>{$t.homeExampleSources(pick.sources)}</span>
            </div>
            <span class="row-stamp"><b>{pick.mentions}</b><span>{$t.stampLabel}</span></span>
          </article>
        {/each}
      </div>
    </section>

    <section class="home-section trust-section">
      <div class="section-heading rule" use:scrollReveal>
        <span class="section-eyebrow">{$t.homeTrustEyebrow}</span>
        <h2>{$t.homeTrustTitle}</h2>
      </div>
      <div class="trust-grid">
        <article use:scrollReveal><span>01</span><h3>{$t.homeTrust1Title}</h3><p>{$t.homeTrust1Desc}</p></article>
        <article use:scrollReveal={{ delay: 90 }}><span>02</span><h3>{$t.homeTrust2Title}</h3><p>{$t.homeTrust2Desc}</p></article>
        <article use:scrollReveal={{ delay: 180 }}><span>03</span><h3>{$t.homeTrust3Title}</h3><p>{$t.homeTrust3Desc}</p></article>
      </div>
    </section>

    <section class="home-final-cta rule" use:scrollReveal>
      <span class="section-eyebrow">{$t.homeFinalEyebrow}</span>
      <h2>{$t.homeFinalTitle}</h2>
      <p>{$t.homeFinalDesc}</p>
      <a class="primary-cta" href="/search" on:click={(event) => navigate(event, '/search')}>
        <span>{$t.homePrimaryCta}</span>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>
      </a>
    </section>
  </main>
{:else}
  <main class="sheet search-page">
    <section class="hero search-hero">
      <p class="hero-kicker" use:scrollReveal>{$t.searchKicker}</p>
      <div class="hero-sentence" use:scrollReveal={{ delay: 70 }}>
        <h1 class="hero-sentence-tail">{$t.heroTail}</h1>
        <form class="hero-search" on:submit|preventDefault={search}>
          <input class="keyword-input" bind:value={keyword} maxlength="80" aria-label={$t.keywordAria} />
          <button class="submit-arrow" type="submit" disabled={loading || !keyword.trim()} aria-label={$t.submitAria}>
            {#if loading}<span class="spinner" aria-hidden="true"></span>{:else}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>{/if}
          </button>
        </form>
      </div>
      <div class="hero-examples" use:scrollReveal={{ delay: 140 }}>
        <span>{$t.examplesLabel}</span>
        {#each searchExamples as example}<button type="button" on:click={() => (keyword = example)}>{example}</button>{/each}
      </div>
      {#if !loading && !result && !overviewResult}
        <p class="search-hint rule" use:scrollReveal={{ delay: 210 }}>{$t.searchHint}</p>
      {/if}
    </section>

    {#if loading}
      <div class="status-line rule" aria-live="polite" use:scrollReveal>
        <span class="caret" aria-hidden="true"></span><span>{$t.progress[progressIndex]}</span><span class="status-note">{$t.statusNote}</span>
      </div>
    {/if}
    {#if error}
      <div class="alert" role="alert" use:scrollReveal>
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 17h.01"/></svg>
        <div><strong>{$t.alertTitle}</strong><span>{error}</span></div><button type="button" on:click={() => (error = '')} aria-label={$t.alertClose}>×</button>
      </div>
    {/if}

    {#if overviewResult}
      <section aria-labelledby="overview-results-title">
        <div class="section-heading rule" use:scrollReveal><span class="section-eyebrow">Area Overview</span><h2 id="overview-results-title">{$t.overviewTitle}</h2><p>{$t.overviewSummary(overviewResult.post_count, overviewResult.regions.length)}</p></div>
        {#if overviewResult.regions.length === 0}
          <div class="empty-state" use:scrollReveal><span>{$t.emptyGlyph}</span><h3>{$t.overviewEmptyTitle}</h3><p>{$t.emptyDesc}</p></div>
        {:else}
          <div class="region-list">
            {#each overviewResult.regions as region, index}
              <article class="region-row" use:scrollReveal={{ delay: Math.min(index * 70, 280) }}>
                <div class="region-title-line"><h3>{region.name}</h3><span class="region-mentions">{$t.regionMentions(region.mention_count)}</span></div>
                <div class="category-tabs">{#each region.categories as category}<button type="button" class="category-tab" on:click={() => exploreCategory(region.name, category.name)}>{category.name}<span class="tab-count">{category.mention_count}</span></button>{/each}</div>
              </article>
            {/each}
          </div>
        {/if}
      </section>
    {/if}

    {#if result}
      <section aria-labelledby="results-title">
        <div class="section-heading rule" use:scrollReveal><span class="section-eyebrow">Your Picks</span><h2 id="results-title">{$t.picksTitle}</h2><p>{$t.picksSummary(result.post_count, result.candidates.length)}</p></div>
        {#if result.candidates.length === 0}
          <div class="empty-state" use:scrollReveal><span>{$t.emptyGlyph}</span><h3>{$t.picksEmptyTitle}</h3><p>{$t.emptyDesc}</p></div>
        {:else}
          <div class="ledger">
            {#each result.candidates as candidate, index}
              <article class:unmatched={!candidate.place} class="ledger-row" use:scrollReveal={{ delay: Math.min(index * 70, 280) }}>
                <span class="row-rank">{String(index + 1).padStart(2, '0')}</span>
                <div class="row-main">
                  <div class="row-title-line"><h3>{candidate.place?.display1 || candidate.name}</h3>{#if !candidate.place}<span class="unmatched-badge">{$t.unmatchedBadge}</span>{/if}</div>
                  {#if candidate.place}
                    <p class="row-address"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s6-5.13 6-11a6 6 0 1 0-12 0c0 5.87 6 11 6 11Z"/><circle cx="12" cy="10" r="2"/></svg>{candidate.place.display2}</p>
                    <div class="row-meta">
                      {#if candidate.place.category}<span>{candidate.place.category.split(' > ').at(-1)}</span>{/if}
                      {#if candidate.place.phone}<span>{candidate.place.phone}</span>{/if}
                      {#if candidate.place.business_hours}<span class="hours" class:closed={!candidate.place.business_hours.is_open}>{candidate.place.business_hours.is_open ? $t.open : $t.closed} · {candidate.place.business_hours.display}</span>{/if}
                      <span>{$t.radiusMeta}</span>
                    </div>
                  {:else}<p class="row-address">{$t.unmatchedAddress(candidate.name)}</p>{/if}
                  <div class="row-footer">
                    {#if candidate.sources.length}
                      <details><summary><span>{$t.sourcesSummary(candidate.sources.length)}</span><svg class="summary-chevron" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg></summary>
                        <div class="sources">{#each candidate.sources as source}<a href={source.url} target="_blank" rel="noreferrer"><span class="source-badge">N</span><span class="source-title">{source.title}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 5h5v5M19 5l-8 8"/><path d="M18 13v5H6V6h5"/></svg></a>{/each}</div>
                      </details>
                    {/if}
                    <div class="link-group">
                      {#if candidate.place?.place_url}<a class="map-link kakao" href={candidate.place.place_url} target="_blank" rel="noreferrer" aria-label={$t.kakaoAria(candidate.place.display1)}><span class="dot"></span>{$t.kakaoLink}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg></a>{/if}
                      {#if candidate.naver_search_url}<a class="map-link naver" href={candidate.naver_search_url} target="_blank" rel="noreferrer" aria-label={$t.naverAria(candidate.place?.display1 || candidate.name)}><span class="dot"></span>{$t.naverLink}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg></a>{/if}
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
  </main>
{/if}

<footer class="sheet" use:scrollReveal>
  <a class="brand" href="/" aria-label={$t.brandHomeAria} on:click={(event) => navigate(event, '/')}>
    <span class="brand-copy"><strong>Placepick</strong></span>
  </a>
  <p>{$t.footerTagline}</p>
</footer>
