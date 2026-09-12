// ==UserScript==
// @name         AI Slop Feed Folder
// @description  Score and fold likely AI slop on X and Reddit, with compact deduplicated scorecards.
// @version      3.0.0
// @match        https://x.com/*
// @match        https://twitter.com/*
// @match        https://www.reddit.com/*
// @match        https://reddit.com/*
// @run-at       document-idle
// ==/UserScript==

(() => {
  'use strict'

  const SCRIPT_KEY = 'sider-ai-slop-v2'
  if (window[`${SCRIPT_KEY}-active`]) return
  window[`${SCRIPT_KEY}-active`] = true

  const isX = /(^|\.)x\.com$|(^|\.)twitter\.com$/.test(location.hostname)
  const strictness = localStorage.getItem('siderAiSlopStrictness') || 'balanced'
  const actionMode = localStorage.getItem('siderAiSlopAction') || 'fold'
  const thresholds = {
    relaxed: { mark: 58, fold: 78, hide: 92 },
    balanced: { mark: 48, fold: 46, hide: 84 },
    aggressive: { mark: 38, fold: 56, hide: 76 },
  }[strictness] || { mark: 48, fold: 46, hide: 84 }

  const processed = new WeakMap()
  const scoredPosts = new Map()
  const calibrationRate = isX ? 0.24 : 0.14
  const calibrationWindow = 300
  const revealedPostStorageKey = 'sider-ai-slop-revealed-posts-v1'
  const textCache = new Map()

  function stablePostId(post) {
    if (!post) return ''
    if (isX) {
      const href = post.querySelector('a[href*="/status/"]')?.getAttribute('href') || ''
      const match = href.match(/\/status\/(\d+)/)
      return match ? `x:${match[1]}` : ''
    }
    const href = post.querySelector('a[href*="/comments/"]')?.getAttribute('href') || ''
    const match = href.match(/\/comments\/([^/]+)/)
    return match ? `reddit:${match[1]}` : ''
  }

  function getRevealedPostIds() {
    try {
      const value = JSON.parse(localStorage.getItem(revealedPostStorageKey) || '[]')
      return new Set(Array.isArray(value) ? value : [])
    } catch {
      return new Set()
    }
  }

  function rememberRevealedPost(post) {
    const id = stablePostId(post)
    if (!id) return
    const ids = getRevealedPostIds()
    ids.add(id)
    localStorage.setItem(revealedPostStorageKey, JSON.stringify([...ids].slice(-1000)))
  }

  function wasPostRevealed(post) {
    const id = stablePostId(post)
    return Boolean(id && getRevealedPostIds().has(id))
  }
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value))
  const countMatches = (text, patterns) => patterns.reduce((sum, pattern) => sum + (pattern.test(text) ? 1 : 0), 0)
  const hasLink = (text, container) => /https?:\/\/|www\.|\b[a-z0-9-]+\.(?:com|io|ai|co|net|org)\b/i.test(text) || !!container?.querySelector('a[href^="http"]')

  const patterns = {
    marketingOpen: [
      /in today(?:'|’)s digital landscape/i,
      /in today(?:'|’)s rapidly evolving (?:digital )?landscape/i,
      /in the ever-evolving landscape of/i,
      /in the fast-paced world of/i,
      /in an era where/i,
    ],
    brandReplace: [
      /\b[A-Z][\w.-]*(?:\s+[A-Z][\w.-]*){0,3}\s+is an?\s+(?:cutting-edge|powerful|top-tier|innovative)\s+(?:tool|platform|solution|app)\b/,
      /\b[A-Z][\w.-]*(?:\s+[A-Z][\w.-]*){0,3}\s+(?:leverages|uses|employs)\s+(?:cutting-edge|AI-powered|AI-driven)\s+(?:AI|technology)\s+to\b/,
      /\b[A-Z][\w.-]*(?:\s+[A-Z][\w.-]*){0,3}\s+(?:is designed to|aims to|enables)\s+(?:empower|streamline|revolutionize|transform)\b/,
      /\b(?:seamlessly|streamlines processes|enhances operational efficiency)\b/i,
    ],
    spam: [
      /\b(?:crypto|nft|airdrop|presale)\b/i,
      /(?:^|\s)\$[A-Z][A-Z0-9]{1,9}\b/,
      /\b(?:onlyfans|telegram|whatsapp)\b/i,
      /\b(?:engagement farming|follow-for-follow|follow 4 follow|f4f)\b/i,
      /(?:^|\s)(?:@\w+[\s,]*){4,}/,
    ],
    generic: [
      /\bdelve into\b/i,
      /\bgame-changer\b/i,
      /\bunlock the (?:full )?power of\b/i,
      /\bseamlessly integrates\b/i,
      /\brobust solution\b/i,
      /\b(?:this )?comprehensive guide\b/i,
      /\bvaluable insights\b/i,
      /\brevolutionize the way\b/i,
      /\bever-evolving landscape\b/i,
      /\bharness the power of\b/i,
      /\bit is important to note\b/i,
      /\bin conclusion\b/i,
      /\bkey takeaways?\b/i,
      /\bto summarize\b/i,
      /\bnavigate the (?:complex|ever-changing) landscape\b/i,
      /\bparadigm shift\b/i,
      /\bholistic approach\b/i,
    ],
    engagement: [
      /\bthoughts\s*\?/i,
      /(?:^|\s)agree\s*\?/i,
      /\bwhat do you think\s*\?/i,
      /\bagree or disagree\s*\?/i,
      /\bam i wrong\s*\?/i,
      /\blet that sink in\b/i,
      /\bread that again\b/i,
      /\b(?:repost if|retweet if you agree|share if you|save this|bookmark this|stop scrolling)\b/i,
      /\bfollow (?:me )?for more\b/i,
      /\b(?:comment below|dm me|link in (?:my )?bio|tag someone|who else)\b/i,
      /\b(?:unpopular opinion|hot take)\b/i,
      /\bmost people don(?:'|’)t (?:realize|understand|know)\b/i,
      /\bnobody is talking about this\b/i,
      /\byour future self will thank you\b/i,
    ],
    firstHand: [
      /\b(?:i tried|i used|my setup|in my case|we tested|i tested|i built|i shipped)\b/i,
    ],
    technical: [
      /\b(?:error log|stack trace|api key|curl|npm run|screenshot|source:|dataset|benchmark)\b/i,
      /github\.com\//i,
      /\b(?:paper|doi):?\s*(?:10\.|https?:\/\/)/i,
    ],
    disagreement: [
      /\b(?:i disagree|not quite|that depends|the tradeoff|counterexample)\b/i,
      /\bhowever\b[^.!?]{0,90}\bbecause\b/i,
    ],
    informal: [
      /\b(?:tbh|imo|idk|fwiw|lol|ugh|honestly|edit:|typo|iirc)\b/i,
    ],
  }

  function addSignal(state, category, points, reason) {
    state.positive += points
    state.categories.add(category)
    state.reasons.push(reason)
  }

  function deductSignal(state, points, reason) {
    state.negative += points
    state.negativeReasons.push(reason)
  }

  function scoreText(rawText, context = {}) {
    const text = rawText.replace(/\u00a0/g, ' ').replace(/[ \t]+/g, ' ').trim()
    const cacheKey = `${context.isReply ? 1 : 0}:${context.hasLink ? 1 : 0}:${text}`
    if (textCache.has(cacheKey)) return textCache.get(cacheKey)

    const words = text.match(/[\p{L}\p{N}_'-]+/gu) || []
    const wordCount = words.length
    const state = { positive: 0, negative: 0, categories: new Set(), reasons: [], negativeReasons: [] }

    const marketingCount = countMatches(text, patterns.marketingOpen)
    const productStructure = /\b(?:tool|platform|solution|app|product|company|service)\b/i.test(text)
    if (marketingCount) addSignal(state, 'marketing-opening', 28, 'marketing opening')

    const brandCount = countMatches(text, patterns.brandReplace)
    if (brandCount) addSignal(state, 'brand-replaceable', clamp(48 + (brandCount - 1) * 4, 48, 56), 'replaceable product pitch')
    if (/\bin recent years\b/i.test(text) && productStructure && brandCount) {
      addSignal(state, 'marketing-opening', 28, 'generic product introduction')
    }

    const spamCount = countMatches(text, patterns.spam)
    if (spamCount) {
      const spamPoints = context.hasLink ? 52 : 40
      addSignal(state, 'platform-spam', spamPoints + Math.min(8, (spamCount - 1) * 4), 'platform spam signal')
    }

    const promotion = scoreUrgentPromotion(text, context)
    if (promotion.points) {
      state.positive += promotion.points
      promotion.categories.forEach(category => state.categories.add(category))
      state.reasons.push(...promotion.reasons)
    }

    const genericCount = countMatches(text, patterns.generic)
    const factualSupport = hasHumanEvidence(text)
    if (genericCount >= 2 && !factualSupport) {
      addSignal(state, 'generic-ai-phrasing', 20 + (genericCount - 2) * 5, `${genericCount} generic phrases`)
    }

    const engagementCount = countMatches(text, patterns.engagement)
    if (engagementCount === 1) addSignal(state, 'engagement-bait', 16, 'engagement bait')
    if (engagementCount >= 2) addSignal(state, 'engagement-bait', 28 + Math.min(8, (engagementCount - 2) * 3), 'stacked engagement bait')

    if (/\b\d+\s+years? ago,?\s+i was\s+(?:broke|fired|rejected|struggling)\b/i.test(text) || /\b(?:rock bottom|nobody believed in me|fast forward|today i (?:run|own|lead))\b/i.test(text)) {
      addSignal(state, 'hero-story', 22, 'template hero story')
    }
    if (/\b(?:[^.!?]{2,50})\s+is not\s+[^.!?]{1,35}\.\s*it(?:'|’)s\s+[^.!?]+/i.test(text) || /\bit(?:'|’)s not about\b[^.!?]+\bit(?:'|’)s about\b/i.test(text) || /\bnot [^,.!?]{2,35},?\s+it(?:'|’)s [^.!?]+/i.test(text)) {
      addSignal(state, 'reversal-template', 14, 'reversal template')
    }
    const listLines = text.split(/\n/).filter(line => /^\s*(?:\d+[.)]|[-•→✓✅])\s+/.test(line)).length
    if (/\bhere are (?:the )?\d+ (?:things|ways|tips|lessons|habits|tools)\b/i.test(text) || /\b\d+ lessons\b/i.test(text) || listLines >= 3) {
      addSignal(state, 'list-template', listLines >= 5 ? 22 : 18, 'template list')
    }
    if (/\b(?:the lesson (?:here )?is|the takeaway|remember this|never give up)\b/i.test(text)) {
      addSignal(state, 'moral-ending', 14, 'preachy ending')
    }
    if (/\b(?:read that again|let that sink in|the irony is|the real (?:question|point) is)\b/i.test(text)) {
      addSignal(state, 'emphasis-template', 12, 'template emphasis')
    }

    const shortBotReply = /^(?:great post|thanks for sharing|this is so true|couldn(?:'|’)t agree more|interesting perspective|well said|love this insight)[.!]*$/i.test(text)
    if (context.isReply && wordCount < 22 && shortBotReply) addSignal(state, 'bot-reply', 12, 'empty short reply')

    const sentences = text.split(/[.!?]+/).map(value => value.trim()).filter(Boolean)
    if (sentences.length >= 4) {
      const lengths = sentences.map(value => (value.match(/[\p{L}\p{N}_'-]+/gu) || []).length)
      const mean = lengths.reduce((a, b) => a + b, 0) / lengths.length
      const variance = lengths.reduce((sum, value) => sum + (value - mean) ** 2, 0) / lengths.length
      if (mean && Math.sqrt(variance) / mean < 0.25) addSignal(state, 'stylometry', 2, 'uniform sentence length')
    }
    if (wordCount > 40 && !/\b\w+(?:n(?:'|’)t|(?:'|’)(?:s|re|ve|ll|d|m))\b/i.test(text)) addSignal(state, 'stylometry', 2, 'unusually formal style')
    const praiseCount = (text.match(/\b(?:excellent|fantastic|brilliant|amazing|incredible|outstanding)\b/gi) || []).length
    if (praiseCount >= 3) addSignal(state, 'stylometry', 2, 'stacked superlatives')
    const emojiCount = (text.match(/\p{Extended_Pictographic}/gu) || []).length
    if (emojiCount >= 5 || (wordCount && emojiCount / wordCount > 0.1)) addSignal(state, 'stylometry', emojiCount >= 8 ? 5 : 2, 'high emoji density')
    const nonEmptyLines = text.split(/\n/).map(value => value.trim()).filter(Boolean)
    if (nonEmptyLines.length > 10 && nonEmptyLines.reduce((sum, value) => sum + value.length, 0) / nonEmptyLines.length < 50) addSignal(state, 'broetry', 5, 'one-line prose')
    if (listLines >= 3) addSignal(state, 'stylometry', listLines >= 6 ? 6 : 3, 'dense bullet structure')
    const namedSpecifics = countSpecifics(text)
    if (wordCount > 110 && namedSpecifics < 3) addSignal(state, 'low-information', 20, 'long but nonspecific')
    if (/\b(?:many companies|many businesses|studies show|research shows|experts say)\b/i.test(text) && !context.hasLink && namedSpecifics < 2) {
      addSignal(state, 'vague-claims', 16, 'unnamed claims')
    }

    if (countMatches(text, patterns.firstHand)) deductSignal(state, 18, 'first-hand experience')
    if (hasConcreteNumber(text)) deductSignal(state, 14, 'concrete numbers or version')
    if (countMatches(text, patterns.technical)) deductSignal(state, 22, 'technical evidence or source')
    if (countMatches(text, patterns.disagreement)) deductSignal(state, 20, 'specific disagreement or tradeoff')
    if (countMatches(text, patterns.informal)) deductSignal(state, 14, 'informal human phrasing')

    if (state.categories.has('promotion-deadline-repeat')) state.negative = Math.min(state.negative, 10)

    const categoryCount = state.categories.size
    const lengthFactor = wordCount < 18 ? 0.9 : wordCount > 160 ? 1.1 : 1
    const multiSignalFactor = categoryCount >= 3 ? 1.1 : categoryCount === 2 ? 1 : 1
    const weakSignalFactor = categoryCount <= 1 && state.positive < 34 ? 0.9 : 1
    const score = clamp(Math.round(state.positive * lengthFactor * multiSignalFactor * weakSignalFactor), 0, 100)
    const result = {
      score,
      reasons: [...new Set(state.reasons)].slice(0, 4),
      positiveReasons: [...new Set(state.reasons)],
      negativeReasons: [...new Set(state.negativeReasons)],
      categories: categoryCount,
      positive: state.positive,
      negative: state.negative,
    }
    if (textCache.size > 1000) textCache.clear()
    textCache.set(cacheKey, result)
    return result
  }

  function scoreUrgentPromotion(text, context = {}) {
    const commercial = /\b(?:sale|discount|deal|promo(?:\s+code)?|coupon|bonus|offer|clearance|bundle|buy|shop|order|checkout|deposit|get yours?|save\s+\d+|\d+%\s*off)\b/i.test(text)
      || /(?:[$€£]\s*\d|\b(?:code|price)\s*[:：]\s*[A-Z0-9-]{3,})/i.test(text)
    if (!commercial) return { points: 0, categories: [], reasons: [] }

    const excludedContext = /\b(?:breaking news|weather alert|evacuation|earthquake|wildfire|hurricane|tornado|flood warning|match|game|tournament|kickoff|polls? close|system (?:alert|warning|maintenance)|security alert)\b/i.test(text)
    if (excludedContext && !/\b(?:buy|shop|order|checkout|promo code|coupon|\d+%\s*off)\b/i.test(text)) {
      return { points: 0, categories: [], reasons: [] }
    }

    const deadlineMatches = text.match(/\b(?:tonight only|today only|ends? (?:today|tonight|soon)|expires?(?: in)? (?:\d+\s*(?:hours?|minutes?)|today|tonight|soon)|last day|for a limited time)\b/gi) || []
    const urgencyMatches = text.match(/\b(?:act now|don(?:'|’)t miss(?: out)?|last chance|hurry|selling fast|while supplies last|only \d+ left|final hours?|now or never)\b/gi) || []
    const hypeMatches = text.match(/\b(?:biggest sale|once in a lifetime|lowest price ever|best deal ever|sale of the year|never (?:to )?be repeated)\b/gi) || []
    const urgencyTotal = deadlineMatches.length + urgencyMatches.length
    const repeatedUrgency = urgencyTotal >= 3 ? 8 : urgencyTotal >= 2 ? 4 : 0

    const letters = text.match(/[A-Za-z]/g) || []
    const uppercase = text.match(/[A-Z]/g) || []
    const uppercaseDensity = letters.length >= 20 && uppercase.length / letters.length >= 0.65
    const uppercaseSegments = text.split(/\n|[.!?]+/).filter(segment => {
      const segmentLetters = segment.match(/[A-Za-z]/g) || []
      const segmentUppercase = segment.match(/[A-Z]/g) || []
      return segmentLetters.length >= 6 && segmentUppercase.length / segmentLetters.length >= 0.75
        && /\b(?:sale|deal|offer|discount|only|ends?|expires?|chance|hurry|off)\b/i.test(segment)
    }).length

    let points = 7
    const categories = ['commercial-promotion']
    const reasons = ['commercial promotion']
    if (deadlineMatches.length) {
      points += 9
      categories.push('promotion-deadline')
      reasons.push('limited-time deadline')
    }
    if (urgencyMatches.length) {
      points += 14
      categories.push('promotion-urgency')
      reasons.push('urgent sales pressure')
    }
    if (hypeMatches.length) {
      points += 6
      categories.push('promotion-hype')
      reasons.push('inflated sales claim')
    }
    if (repeatedUrgency) {
      points += repeatedUrgency
      categories.push('repeated-urgency')
      reasons.push('repeated urgency')
    }
    if (uppercaseDensity) {
      points += 10
      categories.push('uppercase-marketing')
      reasons.push('high uppercase density')
    }
    if (uppercaseSegments >= 3) {
      points += 6
      categories.push('repeated-uppercase')
      reasons.push('repeated uppercase pitches')
    }
    if (context.hasLink) {
      points += 8
      categories.push('commercial-link')
      reasons.push('commercial link')
    }

    if (deadlineMatches.length && repeatedUrgency) {
      points += 8
      categories.push('promotion-deadline-repeat')
      reasons.push('promotion deadline with repeated urgency')
    } else if (deadlineMatches.length) {
      points += 12
      categories.push('promotion-combination')
    } else if (uppercaseDensity || uppercaseSegments >= 3) {
      points += 8
      categories.push('promotion-combination')
    }

    return { points: Math.min(points, 90), categories, reasons }
  }

  function hasConcreteNumber(text) {
    return /(?:\$|€|£)\s?\d|\b\d+(?:\.\d+)?%|\bv?\d+\.\d+(?:\.\d+)?\b|\b\d+\s?(?:ms|gb|mb|tb|kb|fps|rpm|qps)\b|\b(?:19|20)\d{2}\b|\bversion\s+\d/i.test(text)
  }

  function hasHumanEvidence(text) {
    return hasConcreteNumber(text) || countMatches(text, patterns.firstHand) > 0 || countMatches(text, patterns.technical) > 0 || countMatches(text, patterns.disagreement) > 0
  }

  function countSpecifics(text) {
    const numbers = text.match(/\b\d+(?:\.\d+)?(?:%|ms|gb|mb|x)?\b/gi) || []
    const urls = text.match(/https?:\/\/\S+|github\.com\/\S+/gi) || []
    const versions = text.match(/\bv?\d+\.\d+(?:\.\d+)?\b/gi) || []
    const names = text.match(/\b[A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+)+\b/g) || []
    return numbers.length + urls.length + versions.length + names.length
  }

  function getPosts(root = document) {
    if (isX) return [...root.querySelectorAll('article[data-testid="tweet"]')]
    const standard = [...root.querySelectorAll('shreddit-post, article[data-testid="post-container"], div[data-testid="post-container"]')]
    const recent = [...root.querySelectorAll('div[slot="posts"] > .mx-md')].filter(card => {
      const links = card.querySelectorAll('a[href*="/comments/"]')
      return links.length === 1
    })
    return [...new Set([...standard, ...recent])]
  }

  function getText(post) {
    if (isX) {
      const parts = [...post.querySelectorAll('[data-testid="tweetText"]')]
        .map(node => node.innerText?.trim() || '')
        .filter(Boolean)
      return parts.join('\n').trim()
    }
    const titleLink = post.querySelector('a[href*="/comments/"]')
    const title = post.getAttribute('post-title') || post.querySelector('h1,h2,h3,[slot="title"]')?.innerText || titleLink?.innerText || ''
    const body = post.querySelector('[slot="text-body"], [data-click-id="text"], .md')?.innerText || ''
    return `${title}\n${body}`.trim()
  }

  function getAccountTrustAdjustment(post) {
    if (!isX) return { points: 0, reason: '' }
    const icon = post.querySelector('[data-testid="icon-verified"], svg[aria-label*="Verified" i]')
    if (!icon) return { points: 0, reason: '' }
    const svg = icon.matches('svg') ? icon : icon.querySelector('svg')
    if (!svg) return { points: 0, reason: '' }

    const hasGoldGradient = [...svg.querySelectorAll('stop')].some(stop => /#(?:f4e72a|cd8105|cb7b00|f4ec26)/i.test(stop.getAttribute('stop-color') || ''))
    const color = getComputedStyle(svg).color
    const isBlue = /rgb\(29,\s*155,\s*240\)/.test(color)
    if (hasGoldGradient) return { points: 5, reason: 'official organization account' }
    if (!isBlue) return { points: 5, reason: 'government or institution account' }
    return { points: 0, reason: '' }
  }

  function isReply(post) {
    if (!isX) return false
    return !!post.querySelector('[data-testid="socialContext"]') || /replying to/i.test(post.innerText.slice(0, 300))
  }

  function clearPresentation(post) {
    post.classList.remove('sider-ai-slop-marked', 'sider-ai-slop-folded', 'sider-ai-slop-hidden', 'sider-ai-slop-parked')
    post.removeAttribute('aria-hidden')
    post.__siderAiSlopPlaceholder?.remove()
    post.__siderAiSlopPlaceholder = null
    post.querySelector(':scope > .sider-ai-slop-placeholder')?.remove()
    post.querySelector(':scope > .sider-ai-slop-badge')?.remove()
    post.querySelectorAll('.sider-ai-slop-scorecard').forEach(card => card.remove())
  }

  function createScorecard(result) {
    const details = document.createElement('details')
    details.className = `sider-ai-slop-scorecard ${isX ? 'sider-ai-slop-scorecard-x' : 'sider-ai-slop-scorecard-reddit'}`

    const summary = document.createElement('summary')
    const score = document.createElement('strong')
    score.textContent = String(result.score)
    const positive = document.createElement('span')
    positive.className = 'sider-ai-slop-positive'
    positive.textContent = `+${result.positive}`
    const negative = document.createElement('span')
    negative.className = 'sider-ai-slop-negative'
    negative.textContent = `obs ${result.negative}`
    summary.setAttribute('aria-label', `AI slop score ${result.score}, positive ${result.positive}, negative ${result.negative}`)
    summary.append(score, positive, negative)

    const breakdown = document.createElement('div')
    breakdown.className = 'sider-ai-slop-breakdown'
    const groups = [
      ['加分项', result.positiveReasons, 'positive'],
      ['减分项（暂不计入总分）', result.negativeReasons, 'negative'],
    ]
    groups.forEach(([label, reasons, kind]) => {
      const group = document.createElement('section')
      group.className = `sider-ai-slop-group sider-ai-slop-${kind}`
      const heading = document.createElement('b')
      heading.textContent = label
      const list = document.createElement('ul')
      const items = reasons.length ? reasons : ['无']
      items.forEach(reason => {
        const item = document.createElement('li')
        item.textContent = reason
        list.append(item)
      })
      group.append(heading, list)
      breakdown.append(group)
    })
    details.append(summary, breakdown)
    return details
  }

  function present(post, result) {
    if (post.dataset.aiSlopUserRevealed === 'true' || wasPostRevealed(post)) {
      post.dataset.aiSlopUserRevealed = 'true'
      clearPresentation(post)
      return
    }
    clearPresentation(post)
    post.dataset.aiSlopScore = String(result.score)
    const shouldFold = result.score > 21
    post.dataset.aiSlopAction = result.score >= thresholds.hide && actionMode === 'hide' ? 'hide' : shouldFold ? 'fold' : result.score >= thresholds.mark ? 'mark' : 'keep'
    post.dataset.aiSlopCalibrated = result.calibratedFold ? 'true' : 'false'
    post.dataset.aiSlopCalibrationRank = result.calibratedRank ? String(result.calibratedRank) : ''
    post.dataset.aiSlopReasons = result.reasons.join(' | ')
    post.dataset.aiSlopPositive = String(result.positive)
    post.dataset.aiSlopNegative = String(result.negative)

    if (isX && shouldFold && !(actionMode === 'hide' && result.score >= thresholds.hide)) {
      const placeholder = document.createElement('div')
      placeholder.className = 'sider-ai-slop-placeholder sider-ai-slop-standalone-placeholder'
      placeholder.dataset.aiSlopScore = post.dataset.aiSlopScore
      placeholder.dataset.aiSlopAction = 'fold'

      const summary = document.createElement('span')
      summary.className = 'sider-ai-slop-summary'
      const calibrationNote = result.calibratedFold && result.calibrationSize
        ? ` · calibrated top ${Math.round(result.calibrationRate * 100)}% (${result.calibratedRank}/${result.calibrationSize})`
        : ''
      summary.textContent = `AI slop risk ${result.score}${result.reasons.length ? ` · ${result.reasons.join(' · ')}` : ''}${calibrationNote}`

      const reveal = document.createElement('button')
      reveal.type = 'button'
      reveal.className = 'sider-ai-slop-reveal'
      reveal.textContent = 'Reveal'

      const storedHtml = document.createElement('script')
      storedHtml.type = 'text/plain'
      storedHtml.className = 'sider-ai-slop-stored-post'
      storedHtml.textContent = post.outerHTML

      placeholder.append(summary, reveal, storedHtml)
      placeholder.__siderAiSlopOriginalPost = post
      post.__siderAiSlopPlaceholder = placeholder
      post.classList.add('sider-ai-slop-parked')
      post.setAttribute('aria-hidden', 'true')
      post.before(placeholder)
      return
    }

    const scorecard = createScorecard(result)
    if (isX) {
      post.prepend(scorecard)
      const avatar = post.querySelector('[data-testid="Tweet-User-Avatar"]')
      if (avatar) {
        const postRect = post.getBoundingClientRect()
        const avatarRect = avatar.getBoundingClientRect()
        post.style.setProperty('--sider-score-left', `${avatarRect.left + avatarRect.width / 2 - postRect.left}px`)
        post.style.setProperty('--sider-score-top', `${avatarRect.bottom - postRect.top + 4}px`)
      }
    } else {
      const identityRow = post.querySelector('[slot="credit-bar"]')?.firstElementChild?.firstElementChild
      if (identityRow) identityRow.prepend(scorecard)
      else post.prepend(scorecard)
    }

    if (!shouldFold) {
      if (result.score < thresholds.mark) return
      post.classList.add('sider-ai-slop-marked')
      const badge = document.createElement('span')
      badge.className = 'sider-ai-slop-badge'
      badge.textContent = `AI slop risk ${result.score}`
      badge.title = result.reasons.join(', ')
      post.prepend(badge)
      return
    }

    if (actionMode === 'hide' && result.score >= thresholds.hide) {
      post.classList.add('sider-ai-slop-hidden')
      return
    }

    post.classList.add('sider-ai-slop-folded')
    const placeholder = document.createElement('div')
    placeholder.className = 'sider-ai-slop-placeholder'
    const summary = document.createElement('span')
    summary.className = 'sider-ai-slop-summary'
    const calibrationNote = result.calibratedFold && result.calibrationSize
      ? ` · calibrated top ${Math.round(result.calibrationRate * 100)}% (${result.calibratedRank}/${result.calibrationSize})`
      : ''
    summary.textContent = `AI slop risk ${result.score}${result.reasons.length ? ` · ${result.reasons.join(' · ')}` : ''}${calibrationNote}`
    const reveal = document.createElement('button')
    reveal.type = 'button'
    reveal.className = 'sider-ai-slop-reveal'
    reveal.textContent = 'Reveal'
    reveal.addEventListener('click', event => {
      event.preventDefault()
      event.stopPropagation()
      post.dataset.aiSlopUserRevealed = 'true'
      rememberRevealedPost(post)
      scoredPosts.delete(post)
      post.classList.remove('sider-ai-slop-folded')
      placeholder.remove()
    }, { once: true })
    placeholder.append(summary, reveal)
    post.prepend(placeholder)
  }

  function stableTieBreak(text) {
    let hash = 2166136261
    for (let index = 0; index < text.length; index += 1) {
      hash ^= text.charCodeAt(index)
      hash = Math.imul(hash, 16777619)
    }
    return (hash >>> 0) / 4294967295
  }

  function priorRisk(text, result) {
    const words = text.match(/[\p{L}\p{N}_'-]+/gu) || []
    const lines = text.split(/\n/).map(value => value.trim()).filter(Boolean)
    let risk = 0
    if (words.length >= 45) risk += 2
    if (words.length >= 100) risk += 2
    if (lines.length >= 5) risk += 1
    if (/\b(?:here(?:'|’)s how|the truth is|the reality is|most people|everyone|nobody|actually works?|step by step)\b/i.test(text)) risk += 2
    if (/\b(?:streamlin\w*|optimiz\w*|leverag\w*|scalab\w*|actionable|transformative|efficiently)\b/i.test(text)) risk += 2
    if (/\?\s*$/.test(text) && words.length >= 35) risk += 1
    return risk
  }

  function recalibrate() {
    const ranked = [...scoredPosts.values()]
      .sort((a, b) => b.rankScore - a.rankScore)
    const foldCount = Math.round(ranked.length * calibrationRate)
    ranked.forEach((entry, index) => {
      present(entry.post, {
        ...entry.result,
        calibratedFold: false,
        calibratedRank: index + 1,
        calibrationSize: ranked.length,
        calibrationRate,
      })
    })
  }

  function processPost(post) {
    if (post.dataset.aiSlopUserRevealed === 'true' || wasPostRevealed(post)) {
      post.dataset.aiSlopUserRevealed = 'true'
      clearPresentation(post)
      scoredPosts.delete(post)
      return
    }
    const extractedText = getText(post)
    const text = extractedText || '[media-only post]'
    const trust = getAccountTrustAdjustment(post)
    const key = `${text}|${trust.points}|${trust.reason}`
    if (processed.get(post) === key) return
    processed.set(post, key)

    const scored = scoreText(text, { isReply: isReply(post), hasLink: hasLink(text, post) })
    const result = trust.points
      ? {
          ...scored,
          negative: scored.negative + trust.points,
          negativeReasons: [...scored.negativeReasons, trust.reason],
        }
      : scored
    const rankScore = result.score * 100 + priorRisk(text, result) * 10 + stableTieBreak(text)
    scoredPosts.delete(post)
    scoredPosts.set(post, { post, text, result, rankScore })
    while (scoredPosts.size > calibrationWindow) {
      const oldest = scoredPosts.keys().next().value
      scoredPosts.delete(oldest)
    }
    recalibrate()
  }

  function scan(root = document) {
    getPosts(root).forEach(processPost)
  }

  const style = document.createElement('style')
  style.id = 'sider-ai-slop-style-v2'
  style.textContent = `
    .sider-ai-slop-marked { box-shadow: inset 3px 0 0 #d97706 !important; }
    .sider-ai-slop-scorecard { box-sizing: border-box; display: block; width: fit-content; min-width: 0; max-width: calc(100% - 24px); height: auto; margin: 8px 12px 2px; padding: 0; color: inherit; font: 13px/1.35 system-ui, sans-serif; }
    .sider-ai-slop-scorecard > summary > :not(strong),
    .sider-ai-slop-scorecard > .sider-ai-slop-breakdown { display: none !important; }
    .sider-ai-slop-scorecard-x { position: absolute; left: var(--sider-score-left, 20px); top: var(--sider-score-top, 56px); right: auto; bottom: auto; margin: 0; transform: translateX(-50%); z-index: 1; }
    .sider-ai-slop-scorecard > summary { min-width: 26px !important; width: auto !important; min-height: 20px !important; height: 20px !important; padding: 2px 5px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; cursor: default !important; line-height: 1 !important; }
    .sider-ai-slop-scorecard > summary > strong { font: 600 10px/1 system-ui, sans-serif !important; }
    .sider-ai-slop-scorecard-reddit { position: relative; flex: 0 0 auto; margin: 0; max-width: none; z-index: 4; }
    .sider-ai-slop-scorecard-reddit[open] { width: auto; }
    .sider-ai-slop-scorecard-reddit .sider-ai-slop-breakdown { position: absolute; left: 0; top: calc(100% + 4px); width: min(360px, calc(100vw - 32px)); border: 1px solid rgba(83, 100, 113, .3); border-radius: 5px; background: Canvas; color: CanvasText; box-shadow: 0 6px 18px rgba(0, 0, 0, .16); }
    .sider-ai-slop-scorecard > summary { box-sizing: border-box; display: inline-grid; grid-template-columns: repeat(2, minmax(16px, auto)); grid-template-rows: repeat(2, auto); align-items: center; justify-items: center; column-gap: 2px; row-gap: 0; min-width: 39px; min-height: 27px; padding: 2px; border: 1px solid #d97706; border-radius: 5px; color: #92400e; background: #fffbeb; cursor: pointer; list-style: none; user-select: none; }
    .sider-ai-slop-scorecard > summary::-webkit-details-marker { display: none; }
    .sider-ai-slop-scorecard > summary strong { grid-column: 1 / 3; grid-row: 1; margin: 0; font: 600 10px/1.1 system-ui, sans-serif; font-variant-numeric: tabular-nums; }
    .sider-ai-slop-scorecard > summary span { grid-row: 2; font: 600 10px/1.1 system-ui, sans-serif; font-variant-numeric: tabular-nums; }
    .sider-ai-slop-scorecard > summary .sider-ai-slop-positive { grid-column: 1; }
    .sider-ai-slop-scorecard > summary .sider-ai-slop-negative { grid-column: 2; }
    .sider-ai-slop-scorecard .sider-ai-slop-positive { color: #e5484d; }
    .sider-ai-slop-scorecard .sider-ai-slop-negative { color: #2f9e44; }
    .sider-ai-slop-breakdown { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 12px; padding: 8px 10px 10px; border-top: 1px solid rgba(83, 100, 113, .3); }
    .sider-ai-slop-group b { display: block; margin-bottom: 4px; }
    .sider-ai-slop-group ul { margin: 0; padding-left: 18px; }
    .sider-ai-slop-group li { margin: 2px 0; overflow-wrap: anywhere; }
    @media (max-width: 520px) { .sider-ai-slop-breakdown { grid-template-columns: 1fr; } }
    .sider-ai-slop-badge { display: inline-flex; margin: 8px 12px 2px; padding: 3px 7px; border: 1px solid #d97706; border-radius: 5px; color: #92400e; background: #fffbeb; font: 600 12px/1.4 system-ui, sans-serif; }
    .sider-ai-slop-folded { position: relative !important; isolation: isolate; min-height: 52px; overflow: hidden !important; }
    article[data-testid="tweet"].sider-ai-slop-folded { padding-inline: 0 !important; pointer-events: none !important; cursor: default !important; }
    article[data-testid="tweet"].sider-ai-slop-folded .sider-ai-slop-placeholder,
    article[data-testid="tweet"].sider-ai-slop-folded .sider-ai-slop-placeholder * { pointer-events: none !important; cursor: default !important; }
    article[data-testid="tweet"].sider-ai-slop-folded .sider-ai-slop-reveal { pointer-events: auto !important; cursor: pointer !important; }
    article[data-testid="tweet"]:not(.sider-ai-slop-folded) > .sider-ai-slop-placeholder { display: none !important; pointer-events: none !important; }
    .sider-ai-slop-parked { display: none !important; pointer-events: none !important; }
    .sider-ai-slop-folded > :not(.sider-ai-slop-placeholder) { display: none !important; visibility: hidden !important; pointer-events: none !important; }
    .sider-ai-slop-folded:hover > :not(.sider-ai-slop-placeholder),
    .sider-ai-slop-folded:focus-within > :not(.sider-ai-slop-placeholder) { display: none !important; visibility: hidden !important; opacity: 0 !important; pointer-events: none !important; }
    .sider-ai-slop-placeholder { position: relative; z-index: 2147483647; display: flex; align-items: center; justify-content: space-between; gap: 12px; width: 100%; min-height: 52px; box-sizing: border-box; padding: 10px 14px; border: 1px solid #d97706; background: Canvas; color: CanvasText; opacity: 1; pointer-events: auto; font: 13px/1.4 system-ui, sans-serif; }
    .sider-ai-slop-summary { min-width: 0; overflow-wrap: anywhere; }
    .sider-ai-slop-reveal { flex: 0 0 auto; border: 1px solid currentColor; border-radius: 5px; padding: 5px 9px; background: transparent; color: inherit; cursor: pointer; font: 600 12px/1.2 system-ui, sans-serif; }
    .sider-ai-slop-reveal:hover { background: transparent; }
    .sider-ai-slop-hidden { display: none !important; }
  `
  document.head.append(style)

  scan()
  let queued = false
  function replaceFoldedPosts() {
    const selector = isX
      ? 'article[data-testid="tweet"].sider-ai-slop-folded'
      : 'shreddit-post.sider-ai-slop-folded, article.sider-ai-slop-folded'

    document.querySelectorAll(selector).forEach(post => {
      const inlinePlaceholder = post.querySelector(':scope > .sider-ai-slop-placeholder')
      if (!inlinePlaceholder || !post.parentNode) return

      post.classList.remove('sider-ai-slop-folded')
      post.dataset.aiSlopUserRevealed = 'true'
      inlinePlaceholder.remove()
      const restoredHtml = post.outerHTML

      const placeholder = inlinePlaceholder.cloneNode(true)
      placeholder.classList.add('sider-ai-slop-standalone-placeholder')
      placeholder.dataset.aiSlopScore = post.dataset.aiSlopScore || '0'
      placeholder.dataset.aiSlopAction = post.dataset.aiSlopAction || 'fold'

      const storedHtml = document.createElement('script')
      storedHtml.type = 'text/plain'
      storedHtml.className = 'sider-ai-slop-stored-post'
      storedHtml.textContent = restoredHtml
      placeholder.appendChild(storedHtml)
      placeholder.__siderAiSlopOriginalPost = post
      post.classList.add('sider-ai-slop-parked')
      post.setAttribute('aria-hidden', 'true')
      post.before(placeholder)
    })
  }

  document.addEventListener('click', event => {
    const button = event.target.closest?.('.sider-ai-slop-standalone-placeholder .sider-ai-slop-reveal')
    if (!button) return
    event.preventDefault()
    event.stopImmediatePropagation()

    const placeholder = button.closest('.sider-ai-slop-standalone-placeholder')
    const storedHtml = placeholder?.querySelector(':scope > .sider-ai-slop-stored-post')?.textContent
    if (!placeholder || !storedHtml) return

    let restoredPost = placeholder.__siderAiSlopOriginalPost
    if (!restoredPost) {
      const template = document.createElement('template')
      template.innerHTML = storedHtml.trim()
      restoredPost = template.content.firstElementChild
    }
    if (!restoredPost) return
    restoredPost.dataset.aiSlopUserRevealed = 'true'
    rememberRevealedPost(restoredPost)
    scoredPosts.delete(restoredPost)
    restoredPost.classList.remove('sider-ai-slop-folded', 'sider-ai-slop-parked')
    restoredPost.removeAttribute('aria-hidden')
    restoredPost.querySelector(':scope > .sider-ai-slop-placeholder')?.remove()
    placeholder.__siderAiSlopOriginalPost = null
    restoredPost.__siderAiSlopPlaceholder = null
    if (restoredPost.isConnected) placeholder.remove()
    else placeholder.replaceWith(restoredPost)
  }, true)

  siderRuntime.addStyle(`
    .sider-ai-slop-standalone-placeholder { pointer-events: none !important; cursor: default !important; }
    .sider-ai-slop-standalone-placeholder .sider-ai-slop-reveal { pointer-events: auto !important; cursor: pointer !important; }
    .sider-ai-slop-standalone-placeholder .sider-ai-slop-stored-post { display: none !important; }
  `)

  const replacementObserver = new MutationObserver(() => queueMicrotask(replaceFoldedPosts))
  replacementObserver.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] })
  setTimeout(() => replacementObserver.disconnect(), 6 * 60 * 60 * 1000)
  replaceFoldedPosts()

  const observer = new MutationObserver(() => {
    if (queued) return
    queued = true
    setTimeout(() => {
      queued = false
      scan()
    }, 180)
  })
  observer.observe(document.body, { childList: true, subtree: true })
  setTimeout(() => observer.disconnect(), 6 * 60 * 60 * 1000)
})()
