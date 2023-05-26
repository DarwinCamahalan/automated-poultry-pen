import styles from "./navbar.module.scss";
import Image from "next/image";
import icon from "../../public/favicon.png";
import { useEffect, useState } from "react";
import { GiHamburgerMenu } from "react-icons/gi";
import {
  getStorage,
  ref as storageRef,
  listAll,
  getDownloadURL,
} from "firebase/storage";

const Modal = ({ selectedImage, setSelectedImage }) => {
  const closeModal = () => {
    setSelectedImage(null);
  };

  return (
    <>
      <div className={styles.modal} onClick={closeModal}></div>
      <div className={styles.modalContent}>
        <button onClick={closeModal}>Close</button>
        <img src={selectedImage} alt="Selected Image" />
      </div>
    </>
  );
};

const Pagination = ({ currentPage, setCurrentPage, totalPages }) => {
  const pageNumbers = [];

  for (let i = 1; i <= totalPages; i++) {
    pageNumbers.push(i);
  }

  return (
    <div className={styles.pagination}>
      {pageNumbers.map((number) => (
        <button
          key={number}
          onClick={() => setCurrentPage(number)}
          className={currentPage === number ? styles.active : ""}
        >
          {number}
        </button>
      ))}
    </div>
  );
};

const Navbar = () => {
  const [toggle, setToggle] = useState(false);
  const [imageURLs, setImageURLs] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const imagesPerPage = 12;

  useEffect(() => {
    const fetchImageURLs = async () => {
      try {
        const storageInstance = getStorage();
        const imagesRef = storageRef(storageInstance, "images_for_AI"); // Reference to the "images_for_AI" node
        const result = await listAll(imagesRef);

        const imageURLPromises = result.items.map((item) =>
          getDownloadURL(item)
        );
        const urls = await Promise.all(imageURLPromises);
        setImageURLs(urls);
      } catch (error) {
        console.error("Error fetching image URLs:", error);
      }
    };

    fetchImageURLs();
  }, []);

  const indexOfLastImage = currentPage * imagesPerPage;
  const indexOfFirstImage = indexOfLastImage - imagesPerPage;
  const currentImages = imageURLs.slice(indexOfFirstImage, indexOfLastImage);
  const totalPages = Math.ceil(imageURLs.length / imagesPerPage);

  return (
    <>
      {toggle ? (
        <div className={styles.imgContainer}>
          <h1>Images Captured</h1>
          <div className={styles.content}>
            {currentImages.map((url) => {
              const fileName = decodeURIComponent(url)
                .split("/")
                .pop()
                .split("?")[0];
              return (
                <div className={styles.image} key={url}>
                  <img
                    src={url}
                    alt="Image"
                    onClick={() => setSelectedImage(url)}
                  />
                  <p>{fileName}</p>
                </div>
              );
            })}
          </div>
          <Pagination
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            totalPages={totalPages}
          />
        </div>
      ) : null}
      {selectedImage && (
        <Modal
          selectedImage={selectedImage}
          setSelectedImage={setSelectedImage}
        />
      )}
      <div className={styles.navbarBG}>
        <div className={styles.menuContainer}>
          <GiHamburgerMenu onClick={() => setToggle(!toggle)} />
        </div>
        <div className={styles.logo}>
          <div className={styles.layout}>
            <Image
              className={styles.img}
              src={icon}
              alt="Poultry Monitoring System"
            />
            <h1>Poultry Monitoring System</h1>
          </div>
        </div>
      </div>
    </>
  );
};

export default Navbar;
