const logo = new URL('./assets/logo-mark.png', import.meta.url).href

export default function Brand() {
  return <div className="brand"><img className="brand-logo" src={logo} alt=""/><b>漫画下载器</b></div>
}
