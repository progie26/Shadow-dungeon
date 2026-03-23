'use strict';

function svgDataUri(svg) {
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function sigilMarkup(sigil, accent) {
  if (sigil === 'shield') {
    return `<path d="M96 88 L132 104 L126 154 Q96 178 66 154 L60 104 Z" fill="${accent}" fill-opacity="0.26" stroke="${accent}" stroke-width="4"/>`;
  }
  if (sigil === 'orb') {
    return `<circle cx="96" cy="126" r="28" fill="${accent}" fill-opacity="0.18" stroke="${accent}" stroke-width="4"/><path d="M72 126 Q96 98 120 126 Q96 154 72 126 Z" fill="none" stroke="${accent}" stroke-width="4"/>`;
  }
  if (sigil === 'dagger') {
    return `<path d="M96 86 L111 120 L101 120 L101 162 L91 162 L91 120 L81 120 Z" fill="${accent}" stroke="${accent}" stroke-width="4"/>`;
  }
  if (sigil === 'fang') {
    return `<path d="M74 146 Q96 80 118 146" fill="none" stroke="${accent}" stroke-width="6" stroke-linecap="round"/><path d="M76 146 L68 168 M116 146 L124 168" stroke="${accent}" stroke-width="5"/>`;
  }
  if (sigil === 'crown') {
    return `<path d="M58 112 L74 88 L96 106 L118 88 L134 112 L126 130 L66 130 Z" fill="${accent}" fill-opacity="0.22" stroke="${accent}" stroke-width="4"/>`;
  }
  return `<circle cx="96" cy="126" r="26" fill="${accent}" fill-opacity="0.12" stroke="${accent}" stroke-width="4"/>`;
}

function buildTotemSvg(config) {
  const accent = config.accent;
  const eye = config.eye;
  const title = config.title;
  const sigil = config.sigil;
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192" role="img" aria-label="${title}">
      <defs>
        <linearGradient id="bg-${config.key}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#1a2232"/>
          <stop offset="100%" stop-color="#0b1018"/>
        </linearGradient>
        <mask id="mask-${config.key}">
          <rect width="192" height="192" fill="white"/>
        </mask>
        <filter id="glow-${config.key}" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="4" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <rect width="192" height="192" rx="28" fill="url(#bg-${config.key})" mask="url(#mask-${config.key})"/>
      <path d="M24 172 Q96 30 168 172" fill="none" stroke="#20283a" stroke-width="14" stroke-linecap="round"/>
      <circle cx="96" cy="70" r="42" fill="#0f141d" stroke="#30394f" stroke-width="6"/>
      <path d="M52 130 Q96 90 140 130 L134 168 Q96 184 58 168 Z" fill="#131a26" stroke="#34405a" stroke-width="6"/>
      <path d="M70 62 Q96 40 122 62 L122 92 Q96 112 70 92 Z" fill="#1a2130" stroke="#3f4962" stroke-width="5"/>
      <path d="M72 102 Q96 124 120 102" fill="none" stroke="${accent}" stroke-opacity="0.55" stroke-width="4"/>
      <ellipse cx="80" cy="74" rx="10" ry="8" fill="${eye}" filter="url(#glow-${config.key})"/>
      <ellipse cx="112" cy="74" rx="10" ry="8" fill="${eye}" filter="url(#glow-${config.key})"/>
      <path d="M86 88 L96 94 L106 88" fill="none" stroke="${accent}" stroke-width="4" stroke-linecap="round"/>
      ${sigilMarkup(sigil, accent)}
      <path d="M34 154 L58 140 M158 154 L134 140" stroke="${accent}" stroke-opacity="0.48" stroke-width="5" stroke-linecap="round"/>
      <text x="96" y="182" text-anchor="middle" font-family="Georgia, serif" font-size="14" fill="#ced5e6">${title}</text>
    </svg>
  `.replace(/\s+/g, ' ').trim();
  return svgDataUri(svg);
}

function buildTotemArtManifest() {
  return {
    enabled: true,
    classPortraits: {
      warrior: buildTotemSvg({ key: 'warrior', title: '战士', accent: '#d9b46e', eye: '#fff0a8', sigil: 'shield' }),
      mage: buildTotemSvg({ key: 'mage', title: '法师', accent: '#9f7bff', eye: '#efe0ff', sigil: 'orb' }),
      rogue: buildTotemSvg({ key: 'rogue', title: '盗贼', accent: '#7fb7c9', eye: '#dff7ff', sigil: 'dagger' }),
    },
    enemies: {
      skeleton: { src: buildTotemSvg({ key: 'skeleton', title: '骷髅剑士', accent: '#dfd3be', eye: '#ffcf7a', sigil: 'fang' }), title: '骷髅剑士', note: '骨白裂纹图腾，护甲和利牙做成抽象面具。' },
      cultist: { src: buildTotemSvg({ key: 'cultist', title: '暗影教徒', accent: '#9f7bff', eye: '#ffffff', sigil: 'orb' }), title: '暗影教徒', note: '兜帽、符文、单体法术感，保持可爱图腾比例。' },
      rogue: { src: buildTotemSvg({ key: 'enemy-rogue', title: '腐化盗贼', accent: '#7ea8b8', eye: '#ebfaff', sigil: 'dagger' }), title: '腐化盗贼', note: '细长匕首纹章，身形前倾，偏机敏。' },
      wraith: { src: buildTotemSvg({ key: 'wraith', title: '墓园幽魂', accent: '#83d1ff', eye: '#ffffff', sigil: 'orb' }), title: '墓园幽魂', note: '幽火眼睛与漂浮下摆，像幽魂图腾。' },
    },
    bosses: {
      boss_dragon: {
        name: '骨龙',
        src: buildTotemSvg({ key: 'boss-dragon', title: '骨龙', accent: '#f0b162', eye: '#ffe2a3', sigil: 'fang' }),
        tip: '骨龙图腾采用骨翼与火核抽象化，进入二阶段会召唤骷髅。',
      },
      boss_lord: {
        name: '暗影领主',
        src: buildTotemSvg({ key: 'boss-lord', title: '暗影领主', accent: '#a175ff', eye: '#ffffff', sigil: 'crown' }),
        tip: '暗影王冠与黑袍符文做成可爱但压迫的终局图腾。',
      },
    },
  };
}

const NoitaArt = {
  buildTotemSvg,
  buildTotemArtManifest,
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = NoitaArt;
}

if (typeof window !== 'undefined') {
  window.NoitaArt = NoitaArt;
}
