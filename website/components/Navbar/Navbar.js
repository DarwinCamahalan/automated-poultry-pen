import styles from './navbar.module.scss'
import Image from 'next/image'
import icon from '../../public/favicon.png'
const Navbar = () => {
  return (
    <div className={styles.navbarBG}>
      <div className={styles.layout}>
        <Image
        className={styles.img}
        src={icon}
        alt="Poultry Monitoring System"
        />
      <h1>Poultry Monitoring System</h1>
      </div>


    </div>
  )
}

export default Navbar