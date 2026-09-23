import React, { useState, useEffect } from 'react';
import CRlogo from "./GoodCloudResourcingLogo.png";

function App() {
  const [showList1, setShowList1] = useState(false);
  const [showList2, setShowList2] = useState(false);
  const [showList3, setShowList3] = useState(false);
  const [showList4, setShowList4] = useState(false);

  // Function to toggle list visibility
  const toggleLists = () => {
    if (window.innerWidth <= 980) {
      setShowList1(false);
      setShowList2(false);
      setShowList3(false);
      setShowList4(false);
    } else {
        setShowList2(true);
        setShowList1(true);
        setShowList3(true);
      setShowList4(true);
    }
  };

  // Check screen width on component mount
  useEffect(() => {
    toggleLists();
    // Cleanup function
    return () => window.removeEventListener('resize', toggleLists);
  }, []);

  // Check screen width when resized
  useEffect(() => {
    window.addEventListener('resize', toggleLists);
    return () => window.removeEventListener('resize', toggleLists);
  }, [showList1]);

  return (
    <>
    <div className="footer-container">
        <div>
        <button style={{display: window.innerWidth <= 980 ? 'block' : 'none'}} onClick={() =>  {
            setShowList1(!showList1);
            if (!showList1 === true) {
                setShowList2(false);
                setShowList3(false);
                setShowList4(false);
                
            }}}>Job Seekers Menu ▼</button>
        <ul style={{ display: showList1 ? 'block' : 'none' }}>
          <li onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/JobSeekers"} class="footer-nav-options" >Job Seekers Home</li>
          <li onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/JobSeekers/SearchJobs"} class="footer-nav-options addedstyling117">Search Jobs</li>
          <li onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/JobSeekers/SendResume"} class="footer-nav-options addedstyling117" >Send Resume</li>
          <li onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/JobSeekers/WorkForUs"}  class="footer-nav-options addedstyling117" >Work for Cloud Resourcing</li>
        </ul>
        </div>

        <div>
        <button style={{display: window.innerWidth <= 980 ? 'block' : 'none'}} onClick={() =>  {
            setShowList2(!showList2);
            if (!showList2 === true) {
                setShowList1(false);
                setShowList3(false);
                setShowList4(false);
                
            }}}>Employers Menu ▼</button>
        <ul style={{ display: showList2 ? 'block' : 'none' }}>
          <li onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/Employers"} class="footer-nav-options">Employers Home</li>
          <li onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/Employers/HireTalent"} class="footer-nav-options addedstyling117">Hire Talent</li>
        </ul>
        </div>

        <div>
        <button style={{display: window.innerWidth <= 980 ? 'block' : 'none'}} onClick={() =>  {
            setShowList3(!showList3);
            if (!showList3 === true) {
                setShowList1(false);
                setShowList2(false);
                setShowList4(false);
                
            }}}>About Us Menu ▼</button>
        <ul style={{ display: showList3 ? 'block' : 'none' }}>
          <li  onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/AboutUs"} class="footer-nav-options">About Us Home</li>
          <li  onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/AboutUs/WhoWeAre"} class="footer-nav-options addedstyling117">Who We Are</li>
          <li  onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/AboutUs/OurValues"} class="footer-nav-options addedstyling117" >Our Values</li>
          <li onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/AboutUs/OfficeLocations"} class="footer-nav-options addedstyling117" >Office Locations</li>
        </ul>
        </div>

        <div>
        <button style={{display: window.innerWidth <= 980 ? 'block' : 'none'}} onClick={() => {
            setShowList4(!showList4);
            if (!showList4 === true) {
                setShowList1(false);
                setShowList2(false);
                setShowList3(false);
                
            }}}>Contact Us Menu ▼</button>
        <ul style={{ display: showList4 ? 'block' : 'none' }}>
          <li  onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/ContactUs"} class="footer-nav-options">Contact Us Home</li>
          <li onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/JobSeekers/SendResume"} class="footer-nav-options addedstyling117" >Job Seekers</li>
          <li  onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/Employers/HireTalent"} class="footer-nav-options addedstyling117" >Employers</li>
          <li  onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/ContactUs/GeneralRequests"} class="footer-nav-options addedstyling117" > General Requests</li>
        </ul>
        </div>
     
    </div>
    
    <div className="footer-bottom">
        <img onMouseEnter={(e) => e.currentTarget.style.cursor = 'pointer'} onClick={() => window.location.href="/"} src={CRlogo} alt="cloud resourcing logo"/>
            <p>jobs@cloudresourcing.net</p>
            <p>Copyright &copy; 2024 Cloud Resourcing</p>
            </div>
    </>
  );
}

export default App;


/*import logo from "./GoodCloudResourcingLogo.png";
import "./layout.css";
function Footer() {
  return (
    <div class="footer-container">
        <div class="footer-menu-container">
        <div>
            <h3>Job Seeker Solutions</h3>
            <ul>
                <li>Search Jobs</li>
                <li>Send Resume</li>
                <li>Work for Cloud Resourcing</li>
            </ul>

        </div>
        <div>
            <h3>Employer Solutions</h3>
            <ul>
                <li>Hire Talent</li>
            </ul>

        </div>
        <div>
            <h3>About Us</h3>
            <ul>
                <li>Who We Are</li>
                <li>Our Values</li>
                <li>Office Locations</li>
            </ul>
        </div>
        <div>
            <h3>Contact Us</h3>
            <ul>
                <li>Job Seekers</li>
                <li>Employers</li>
                <li>General Requests</li>
            </ul>
        </div>    
        </div>
        
    <div class="bottom"> 
        <div>
        <img src={logo} alt="Cloud Resourcing Logo"></img>
        <p>CLOUD RESOURCING</p>
        </div>
        <p>200 Front St. W. Toronto</p>
        <p>jobs@cloudresourcing.net</p>
        <p>Copyright © 2022 Cloud Resourcing</p>
    </div>
    </div>
    
  );
}

export default Footer;

*/