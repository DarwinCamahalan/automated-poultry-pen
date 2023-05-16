
import Head from 'next/head'
import Navbar from '../components/Navbar/Navbar.js'
const Home = () => {


  return (
    <>
      <Head>
        <title>Poultry Monitoring System</title>
        <link rel="icon" type="image/png" href="/favicon.png" />
      </Head>
      <div >
      <Navbar/>
      </div>
    </>
  )
}

export default Home