import React, { useEffect, useMemo, useRef, useState } from 'react'

const BACKEND = import.meta.env.VITE_BACKEND_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000')

function parseChannel(input){
  try{
    if(!input) return ''
    const u = new URL(input.includes('://') ? input : 'https://www.twitch.tv/'+input)
    return u.pathname.replace(/^\//,'').split('/')[0] || ''
  }catch{ return input.replace(/^#/,'') }
}

function Chat({messages}){
  const ref = useRef(null)
  useEffect(()=>{ if(ref.current) ref.current.scrollTop = ref.current.scrollHeight },[messages])
  return <div className="chat" ref={ref}>
    {messages.map((m,i)=>(<div key={i} className="msg"><b>{m.user}{m.subscriber?'⭐':''}:</b> {m.text}</div>))}
  </div>
}

function FollowsModal({open, data, onClose}){
  if(!open) return null
  const items = data?.follows || []
  return <div className="modal-backdrop">
    <div className="modal">
      <div className="modal-header"><b>Подписки {data?.user}</b> (всего: {items.length})</div>
      <div className="modal-body">
        <div className="f-grid">
          {items.map((it,i)=>(<div key={i} className="f-card">
            <div className="f-row">
              {it.avatar ? <img src={it.avatar} alt=""/> : null}
              <div>
                <a href={it.channel_url} target="_blank" rel="noreferrer">{it.channel}</a>
                <div style={{opacity:.7,fontSize:12}}>{it.followed_at || '—'}</div>
              </div>
            </div>
          </div>))}
          {!items.length && <div style={{opacity:.7}}>Ничего не нашли</div>}
        </div>
      </div>
      <div className="modal-footer"><button onClick={onClose}>Закрыть</button></div>
    </div>
  </div>
}

export default function App(){
  const [url, setUrl] = useState('')
  const [keyword, setKeyword] = useState('+')
  const [messages, setMessages] = useState([])
  const [participants, setParticipants] = useState([])
  const [winner, setWinner] = useState(null)
  const [fopen, setFOpen] = useState(false)
  const [fdata, setFData] = useState(null)
  const esRef = useRef(null)
  const channel = useMemo(()=>parseChannel(url),[url])

  useEffect(()=>{ document.title = channel ? `Главарь Тусовки ${channel}` : 'ЛУДИК БОТ' },[channel])

  const connect = (withKw=true)=>{
    if(!channel) return alert('Укажи канал Twitch')
    if(esRef.current){ esRef.current.close(); esRef.current=null }
    const u = new URL(BACKEND+'/api/chat/stream')
    u.searchParams.set('channel', channel)
    if(withKw && keyword) u.searchParams.set('keyword', keyword)
    const es = new EventSource(u.toString())
    es.onmessage = ev => { try{ const d = JSON.parse(ev.data); setMessages(m=>[...m, d].slice(-400)) }catch{} }
    es.onerror = () => console.warn('SSE error')
    esRef.current = es
  }

  const refresh = async()=>{
    if(!channel) return
    const r = await fetch(`${BACKEND}/api/participants?channel=${encodeURIComponent(channel)}`)
    const data = await r.json()
    setParticipants(data.participants||[])
  }

  const clear = async()=>{
    if(!channel) return
    await fetch(`${BACKEND}/api/participants/clear?channel=${encodeURIComponent(channel)}`, {method:'POST'})
    setParticipants([])
  }

  const pick = async()=>{
    if(!channel) return
    const r = await fetch(`${BACKEND}/api/winner?channel=${encodeURIComponent(channel)}`, {method:'POST'})
    const data = await r.json()
    if(!data.winner) return alert('Нет участников')
    setWinner(data.winner)
  }

  const exportCSV = ()=>{
    if(!channel) return
    window.open(`${BACKEND}/api/export?channel=${encodeURIComponent(channel)}`,'_blank')
  }

  const checkFollows = async()=>{
    if(!winner) return
    const r = await fetch(`${BACKEND}/api/follows_lookup?user=${encodeURIComponent(winner)}`)
    const data = await r.json()
    setFData(data); setFOpen(true)
  }

  return <div className="container">
    <header><div className="brand">ЛУДИК БОТ</div><div style={{opacity:.7}}>by @TRAVISPERKIIINS &lt;3</div></header>
    <section className="controls">
      <input placeholder="Ссылка или имя канала Twitch" value={url} onChange={e=>setUrl(e.target.value)} />
      <input placeholder="Ключевое слово (точное)" value={keyword} onChange={e=>setKeyword(e.target.value)} />
      <button onClick={()=>connect(true)}>Подключиться</button>
      <button onClick={()=>connect(false)}>Без ключевого</button>
      <button onClick={refresh}>Обновить участников</button>
      <button onClick={clear}>Сбросить участников</button>
      <button onClick={pick}>Выбрать победителя</button>
      <button onClick={exportCSV}>Экспорт CSV</button>
      {winner && <button onClick={checkFollows}>Проверить подписки победителя</button>}
    </section>
    <main className="grid">
      <div className="panel">
        <h3>Чат {channel?`#${channel}`:''}</h3>
        <Chat messages={messages} />
      </div>
      <div className="panel">
        <h3>Участники ({participants.length})</h3>
        <ul>{participants.map(p=>(<li key={p.username}>{p.subscriber?'⭐ ':''}{p.username}{p.last_win_at?` — посл.победа: ${new Date(p.last_win_at).toLocaleString()}`:''}</li>))}</ul>
      </div>
    </main>
    <FollowsModal open={fopen} data={fdata} onClose={()=>setFOpen(false)} />
  </div>
}
