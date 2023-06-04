import AllGraphs from "@/components/Graphs/AllGraphs";
import Navbar from "@/components/Navbar/Navbar";

import Head from "next/head";
const Graphs = () => {
  return (
    <>
      <Head>
        <title>Line Charts</title>
        <link rel="icon" type="image/png" href="/favicon.png" />
      </Head>
      <Navbar />
      <AllGraphs />
    </>
  );
};

export default Graphs;
