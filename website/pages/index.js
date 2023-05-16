
import Head from 'next/head'
import Navbar from '../components/Navbar/Navbar.js'
import Content from '@/components/Content/Content.js'
const Home = () => {


  return (
    <>
      <Head>
        <title>Poultry Monitoring System</title>
        <link rel="icon" type="image/png" href="/favicon.png" />
      </Head>
      <div >
      <Navbar/>
      <Content/>
      </div>
    </>
  )
}

export default Home