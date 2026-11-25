import { useState } from 'react'
import './App.css'

type WindowSize = 5 | 10
type ActivityKind = 'accel' | 'brake' | 'rest' | 'mixed'

type Interval = {
  label: string
  hr: number
  estimate: number
  delta: number
  load: number
  recovery: number
  x1: number
  x2: number
  x3: number
  x4: number
  x5: number
  kind: ActivityKind
}

type GlyphName = 'grid' | 'chart' | 'users' | 'file' | 'download' | 'info' | 'arrow'

const intervals5: Interval[] = [
  { label: '0–5分', hr: 148, estimate: 150, delta: 4.2, load: 38, recovery: 2, x1: 22, x2: 14, x3: 31, x4: 3, x5: 48, kind: 'mixed' },
  { label: '5–10分', hr: 157, estimate: 155, delta: 8.1, load: 62, recovery: 0, x1: 44, x2: 27, x3: 54, x4: 6, x5: 29, kind: 'accel' },
  { label: '10–15分', hr: 166, estimate: 164, delta: 6.6, load: 71, recovery: -1, x1: 51, x2: 34, x3: 66, x4: 8, x5: 18, kind: 'accel' },
  { label: '15–20分', hr: 162, estimate: 164, delta: -3.3, load: 47, recovery: -5, x1: 28, x2: 31, x3: 42, x4: 3, x5: 66, kind: 'rest' },
  { label: '20–25分', hr: 171, estimate: 169, delta: 8.7, load: 78, recovery: 0, x1: 64, x2: 39, x3: 72, x4: 10, x5: 12, kind: 'accel' },
  { label: '25–30分', hr: 176, estimate: 178, delta: 5.1, load: 83, recovery: 1, x1: 68, x2: 49, x3: 79, x4: 12, x5: 8, kind: 'brake' },
  { label: '30–35分', hr: 168, estimate: 166, delta: -7.8, load: 41, recovery: -7, x1: 24, x2: 22, x3: 37, x4: 2, x5: 77, kind: 'rest' },
  { label: '35–40分', hr: 174, estimate: 175, delta: 6.3, load: 69, recovery: 0, x1: 49, x2: 42, x3: 63, x4: 7, x5: 22, kind: 'mixed' },
  { label: '40–45分', hr: 181, estimate: 179, delta: 7.2, load: 88, recovery: 1, x1: 72, x2: 45, x3: 84, x4: 14, x5: 4, kind: 'brake' },
  { label: '45–50分', hr: 176, estimate: 177, delta: -4.8, load: 55, recovery: -4, x1: 35, x2: 29, x3: 48, x4: 4, x5: 53, kind: 'rest' },
  { label: '50–55分', hr: 184, estimate: 182, delta: 8.0, load: 91, recovery: 2, x1: 77, x2: 51, x3: 87, x4: 15, x5: 5, kind: 'accel' },
  { label: '55–60分', hr: 178, estimate: 180, delta: -5.9, load: 52, recovery: -6, x1: 31, x2: 36, x3: 44, x4: 5, x5: 61, kind: 'rest' },
]

const intervals10: Interval[] = [
  { label: '0–10分', hr: 157, estimate: 156, delta: 7.1, load: 50, recovery: 1, x1: 33, x2: 21, x3: 42, x4: 5, x5: 38, kind: 'mixed' },
  { label: '10–20分', hr: 162, estimate: 163, delta: 2.6, load: 59, recovery: -2, x1: 40, x2: 33, x3: 54, x4: 5, x5: 42, kind: 'mixed' },
  { label: '20–30分', hr: 176, estimate: 174, delta: 6.8, load: 81, recovery: 1, x1: 66, x2: 44, x3: 76, x4: 11, x5: 10, kind: 'accel' },
  { label: '30–40分', hr: 174, estimate: 171, delta: -1.5, load: 55, recovery: -4, x1: 37, x2: 31, x3: 50, x4: 4, x5: 51, kind: 'rest' },
  { label: '40–50分', hr: 176, estimate: 178, delta: 2.7, load: 72, recovery: -1, x1: 55, x2: 38, x3: 66, x4: 9, x5: 31, kind: 'brake' },
  { label: '50–60分', hr: 178, estimate: 181, delta: 2.1, load: 69, recovery: -2, x1: 54, x2: 43, x3: 65, x4: 10, x5: 33, kind: 'mixed' },
]

const featureBars = [
  { key: 'x1', label: '加速', note: 'x1', value: 82, color: 'coral', impact: '+4.8拍' },
  { key: 'x2', label: '減速', note: 'x2', value: 64, color: 'blue', impact: '+2.7拍' },
  { key: 'x3', label: '体の揺れ', note: 'x3', value: 58, color: 'teal', impact: '+2.1拍' },
  { key: 'x4', label: '衝撃', note: 'x4', value: 38, color: 'gold', impact: '+0.8拍' },
  { key: 'x5', label: '停止・回復', note: 'x5', value: 46, color: 'ink', impact: '−3.4拍' },
]

function Glyph({ name }: { name: GlyphName }) {
  const paths: Record<GlyphName, string> = {
    grid: 'M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z',
    chart: 'M4 18V6m0 12h16M7 15l3-4 3 2 5-7',
    users: 'M16 20v-1.5a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4V20m6-9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm6-5a3 3 0 0 1 0 5.8M17 14.5a4 4 0 0 1 4 4V20',
    file: 'M6 3h8l4 4v14H6zM14 3v5h5M9 13h6M9 17h6',
    download: 'M12 3v12m0 0 4-4m-4 4-4-4M4 20h16',
    info: 'M12 17v-5m0-4h.01M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z',
    arrow: 'M5 12h14m-5-5 5 5-5 5',
  }
  return (
    <svg className="glyph" viewBox="0 0 24 24" aria-hidden="true">
      <path d={paths[name]} />
    </svg>
  )
}

function formatSigned(value: number): string {
  return `${value >= 0 ? '+' : '−'}${Math.abs(value).toFixed(1)}`
}

function Chart({ data, selectedIndex, onSelect }: { data: Interval[]; selectedIndex: number; onSelect: (index: number) => void }) {
  const width = 760
  const height = 276
  const padding = { top: 24, right: 22, bottom: 42, left: 42 }
  const min = 140
  const max = 190
  const x = (index: number) => padding.left + (index / (data.length - 1)) * (width - padding.left - padding.right)
  const y = (value: number) => padding.top + ((max - value) / (max - min)) * (height - padding.top - padding.bottom)
  const estimatePath = data.map((item, index) => `${x(index)},${y(item.estimate)}`).join(' ')

  return (
    <div className="chart-wrap">
      <svg className="heart-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="区間ごとの心拍とモデル推定値の推移">
        {[140, 150, 160, 170, 180, 190].map((tick) => (
          <g key={tick}>
            <line className="chart-grid" x1={padding.left} x2={width - padding.right} y1={y(tick)} y2={y(tick)} />
            <text className="chart-label" x={padding.left - 12} y={y(tick) + 4} textAnchor="end">{tick}</text>
          </g>
        ))}
        <polyline className="estimate-line" points={estimatePath} />
        {data.slice(0, -1).map((item, index) => {
          const next = data[index + 1]
          const tone = item.kind === 'accel' ? '#ef6b64' : item.kind === 'brake' ? '#5d8fd6' : item.kind === 'rest' ? '#1b2934' : '#83a9d7'
          return <line key={`${item.label}-line`} className="hr-segment" stroke={tone} x1={x(index)} y1={y(item.hr)} x2={x(index + 1)} y2={y(next.hr)} />
        })}
        {data.map((item, index) => (
          <g key={item.label} onClick={() => onSelect(index)} className="chart-point-group">
            <circle className={`chart-point ${selectedIndex === index ? 'selected' : ''}`} cx={x(index)} cy={y(item.hr)} r={selectedIndex === index ? 6 : 4} />
            <text className="chart-x-label" x={x(index)} y={height - 13} textAnchor="middle">{item.label.split('–')[0]}</text>
          </g>
        ))}
      </svg>
      <div className="chart-caption">
        <span><i className="legend-dot heart" />実測心拍</span>
        <span><i className="legend-line" />モデル推定</span>
        <span className="caption-note">色は区間内で目立った動きを表示</span>
      </div>
    </div>
  )
}

function App() {
  const [windowSize, setWindowSize] = useState<WindowSize>(5)
  const [selectedIndex, setSelectedIndex] = useState(8)
  const [activeNav, setActiveNav] = useState('サマリー')
  const data = windowSize === 5 ? intervals5 : intervals10
  const selected = data[Math.min(selectedIndex, data.length - 1)]
  const displayIndex = Math.min(selectedIndex, data.length - 1)

  const downloadCsv = () => {
    const header = '区間,実測心拍,推定心拍,心拍変化,負荷スコア,停止・回復秒\n'
    const rows = data.map((item) => `${item.label},${item.hr},${item.estimate},${item.delta},${item.load},${item.x5}`).join('\n')
    const blob = new Blob([header + rows], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `heart-response-${windowSize}min.csv`
    anchor.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark"><span /></div>
          <div><strong>PULSE</strong><small>心拍応答モデル</small></div>
        </div>
        <div className="workspace-label">チーム分析ワークスペース</div>
        <nav className="main-nav" aria-label="メインナビゲーション">
          {[
            { label: 'サマリー', icon: 'grid' as GlyphName },
            { label: '区間分析', icon: 'chart' as GlyphName },
            { label: '選手比較', icon: 'users' as GlyphName },
            { label: '検証レポート', icon: 'file' as GlyphName },
          ].map((item) => (
            <button key={item.label} className={activeNav === item.label ? 'active' : ''} onClick={() => setActiveNav(item.label)}>
              <Glyph name={item.icon} />{item.label}
              {item.label === '区間分析' && <span className="nav-badge">NEW</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-footnote">
          <div className="mini-pulse"><span /></div>
          <p>データは機密として扱われます</p>
          <small>この画面は分析方法を体験するためのデモです。</small>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumbs"><span>チーム分析</span><b>/</b><strong>{activeNav}</strong></div>
          <div className="topbar-actions">
            <span className="sync-status"><i />デモデータで表示中</span>
            <a className="project-download" href="/project-files.zip" download="pulse-project-files.zip"><Glyph name="download" />プロジェクトZIP</a>
            <button className="avatar" aria-label="ユーザーメニュー">TS</button>
          </div>
        </header>

        <div className="content-inner">
          <section className="hero-row">
            <div>
              <div className="eyebrow">HEART-RATE RESPONSE MODEL <span>v0.1</span></div>
              <h1>負荷と回復の関係を、<br /><em>ひとつの画面で。</em></h1>
              <p className="hero-copy">心拍の変化を、加速・減速・体の揺れ・衝撃・停止時間から読み解きます。</p>
            </div>
            <div className="hero-summary">
              <div className="summary-orbit"><div className="orbit-core"><strong>5</strong><span>試合</span></div></div>
              <div><span className="summary-kicker">対象データ</span><strong>選手A・選手B</strong><small>心拍が安定して記録された試合</small></div>
            </div>
          </section>

          <div className="filter-row">
            <div className="filter-group">
              <label>選手</label>
              <button className="select-button">選手B <span>⌄</span></button>
            </div>
            <div className="filter-group">
              <label>試合</label>
              <button className="select-button wide">2025.10.15　リーグ戦 <span>⌄</span></button>
            </div>
            <div className="filter-group window-filter">
              <label>区切り幅</label>
              <div className="segmented-control">
                <button className={windowSize === 5 ? 'selected' : ''} onClick={() => { setWindowSize(5); setSelectedIndex(8) }}>5分</button>
                <button className={windowSize === 10 ? 'selected' : ''} onClick={() => { setWindowSize(10); setSelectedIndex(3) }}>10分</button>
              </div>
            </div>
            <button className="export-button" onClick={downloadCsv}><Glyph name="download" />CSVを書き出す</button>
          </div>

          <section className="metric-grid" aria-label="主要指標">
            <div className="metric-card highlight"><div className="metric-top"><span>平均心拍</span><span className="metric-icon heart-icon">♥</span></div><strong>171 <small>bpm</small></strong><div className="metric-trend positive">+3.8% <span>前試合比</span></div></div>
            <div className="metric-card"><div className="metric-top"><span>最高心拍</span><span className="metric-icon">↑</span></div><strong>188 <small>bpm</small></strong><div className="metric-sub">50–55分区間で記録</div></div>
            <div className="metric-card"><div className="metric-top"><span>平均心拍変化</span><span className="metric-icon teal-icon">↗</span></div><strong>+6.8 <small>bpm</small></strong><div className="metric-trend positive">負荷に反応して上昇</div></div>
            <div className="metric-card"><div className="metric-top"><span>回復係数 <b className="info-dot">i</b></span><span className="metric-icon recovery-icon">↘</span></div><strong>−0.24 <small>c</small></strong><div className="metric-trend positive">回復の傾向あり</div></div>
          </section>

          <section className="panel chart-panel">
            <div className="panel-heading">
              <div><div className="section-kicker">01 / RESPONSE OVER TIME</div><h2>心拍の変化とモデル推定</h2><p>色分けされた線で、どの動きのあとに心拍が変わったかを確認できます。</p></div>
              <div className="chart-reading"><span className="reading-dot" />選択中 <strong>{selected.label}</strong><b>{formatSigned(selected.delta)} bpm</b></div>
            </div>
            <Chart data={data} selectedIndex={displayIndex} onSelect={setSelectedIndex} />
            <div className="chart-callout"><div className="callout-tag">SELECTED INTERVAL</div><strong>{selected.label}</strong><span>{selected.kind === 'brake' ? '濃い青の減速が集中' : selected.kind === 'rest' ? '停止時間が長く、回復が見られる' : '加速による負荷が心拍に反映'}</span><b>{selected.hr} <small>bpm</small></b></div>
          </section>

          <div className="dashboard-grid">
            <section className="panel feature-panel">
              <div className="panel-heading compact"><div><div className="section-kicker">02 / FEATURE CONTRIBUTION</div><h2>心拍に効いた動き</h2></div><button className="text-button">詳しく見る <Glyph name="arrow" /></button></div>
              <p className="panel-intro">段階1の推定値を、5つの特徴量ごとに表示しています。</p>
              <div className="feature-list">
                {featureBars.map((feature) => <div className="feature-row" key={feature.key}><div className="feature-label"><strong>{feature.label}</strong><span>{feature.note}</span></div><div className="feature-track"><div className={`feature-fill ${feature.color}`} style={{ width: `${feature.value}%` }} /></div><strong className="feature-impact">{feature.impact}</strong></div>)}
              </div>
              <div className="feature-foot"><span><i className="tiny-dot coral" />心拍を上げる</span><span><i className="tiny-dot ink" />心拍を下げる</span><span className="feature-foot-note">推定値は参考値です</span></div>
            </section>

            <section className="panel insight-panel">
              <div className="panel-heading compact"><div><div className="section-kicker">03 / STAFF NOTE</div><h2>今日の読み解き</h2></div><span className="confidence-chip">信頼度 参考</span></div>
              <div className="insight-main"><div className="insight-number">01</div><div><strong>加速のあと、心拍が<br />しっかり上がっています。</strong><p>特に20–30分、50–55分区間で負荷と心拍の動きが揃っています。</p></div></div>
              <div className="insight-divider" />
              <div className="insight-secondary"><span className="insight-arrow">↘</span><div><strong>停止時間が長い区間では回復</strong><p>30–35分区間では、停止77秒に対して心拍が−7.8 bpm。</p></div></div>
              <div className="caution-note"><Glyph name="info" /><span>このモデルは負荷に対する心拍の反応を示すもので、けがの予測ではありません。</span></div>
            </section>
          </div>

          <section className="panel table-panel">
            <div className="panel-heading compact"><div><div className="section-kicker">04 / INTERVAL DETAIL</div><h2>区間ごとの分析</h2></div><div className="table-tools"><span>全 {data.length} 区間</span><button className="filter-button">フィルター　⌄</button></div></div>
            <div className="table-scroll"><table><thead><tr><th>区間</th><th>実測心拍</th><th>推定心拍</th><th>心拍変化</th><th>負荷</th><th>停止・回復</th><th>主な動き</th></tr></thead><tbody>{data.map((item, index) => <tr key={item.label} className={displayIndex === index ? 'active-row' : ''} onClick={() => setSelectedIndex(index)}><td><strong>{item.label}</strong></td><td>{item.hr} <small>bpm</small></td><td>{item.estimate} <small>bpm</small></td><td className={item.delta >= 0 ? 'cell-up' : 'cell-down'}>{formatSigned(item.delta)}</td><td><div className="load-cell"><span>{item.load}</span><i><b style={{ width: `${item.load}%` }} /></i></div></td><td className={item.x5 > 50 ? 'cell-down' : ''}>{item.x5}秒</td><td><span className={`activity-pill ${item.kind}`}>{item.kind === 'accel' ? '加速' : item.kind === 'brake' ? '減速' : item.kind === 'rest' ? '停止' : '複合'}</span></td></tr>)}</tbody></table></div>
          </section>

          <footer className="page-footer"><span>心拍応答モデル　/　分析方法の説明に基づくプロトタイプ</span><span>© PULSE ANALYTICS</span></footer>
        </div>
      </main>
    </div>
  )
}

export default App
