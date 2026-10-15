import logo from "./GoodCloudResourcingLogo.png";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars } from '@fortawesome/free-solid-svg-icons';
import './layout.css';
import { useState, useEffect } from "react";

function Nav() {
    /*NEW CODE-----------------------------------------------------------------------------------*/












    /*OLD CODE-----------------------------------------------------------------------------------*/
    const [showMenu, setShowMenu] = useState(false);


        const [windowWidth, setWindowWidth] = useState(window.innerWidth);
      
        useEffect(() => {
          const handleResize = () => setWindowWidth(window.innerWidth);
      
          window.addEventListener('resize', handleResize);
      
          // Cleanup event listener on component unmount
          return () => window.removeEventListener('resize', handleResize);
        }, []);


    return (
        <nav>
            <div className="content">
            <div className="bars">

    <FontAwesomeIcon icon={faBars} className="barsicon" onClick={() => setShowMenu(!showMenu)}/>
            </div>
            
                <div className="home">
                    <img onClick={() => window.location.href="/"}className="CRlogo" src={logo}></img>
                    <div onClick={() => window.location.href = "/"} className="logo"><a href="/">CloudResourcing</a> </div>
                </div>

                
                <div className="links" style={{ display: showMenu ? "" : "none" }}>
                <li><a href="/JobSeekers">Job Seekers</a> 
                <ul style={{display: windowWidth <= 980? 'none' : ''}}>
                    <li ><a href="/JobSeekers/SearchJobs">Search Jobs</a></li> 
                    <li><a href="/JobSeekers/SendResume">Send Resume</a></li>
                    <li><a href="/JobSeekers/WorkForUs">Work for Cloud Resourcing</a></li>
                </ul>
                </li>

                {/*NAV BAR EXPERIMENT */}
                <li style={{display: windowWidth <= 980? '' : 'none', paddingLeft: '25px'}} ><a class="submenus" href="/JobSeekers/SearchJobs">Search Jobs</a></li> 
                    <li  style={{display: windowWidth <= 980? '' : 'none', paddingLeft: '25px'}}><a class="submenus" href="/JobSeekers/SendResume">Send Resume</a></li>
                    <li style={{display: windowWidth <= 980? '' : 'none', paddingLeft: '25px'}}><a class="submenus"href="/JobSeekers/WorkForUs">Work for Cloud Resourcing</a></li>


                
                <li><a href="/Employers">Employers</a>
                <ul style={{display: windowWidth <= 980? 'none' : ''}}>
                     <li><a href="/Employers/HireTalent">Hire Talent</a></li>
                </ul></li>
                <li style={{display: windowWidth <= 980? '' : 'none', paddingLeft: '25px'}} ><a class="submenus" href="/Employers/HireTalent">Hire Talent</a></li> 

                <li><a href='/AboutUs'>About Us</a>
                <ul style={{display: windowWidth <= 980? 'none' : ''}}>
                    <li><a href="/AboutUs/WhoWeAre">Who We Are</a></li>
                    <li><a href="/AboutUs/OurValues">Our Values</a></li>
                    <li><a href="/AboutUs/OfficeLocations">Office Locations</a></li>
                    <li><a href="/AboutUs/Login">Login</a></li> {/* This block of code was added */}
                </ul>
                </li>
                  {/*NAV BAR EXPERIMENT */}
                  <li style={{display: windowWidth <= 980? '' : 'none', paddingLeft: '25px'}} ><a class="submenus" href="/AboutUs/WhoWeAre">Who We Are</a></li> 
                    <li  style={{display: windowWidth <= 980? '' : 'none', paddingLeft: '25px'}}><a class="submenus" href="/AboutUs/OurValues">Our Values</a></li>
                    <li style={{display: windowWidth <= 980? '' : 'none', paddingLeft: '25px'}}><a class="submenus" href="/AboutUs/OfficeLocations">Office Locations</a></li>
                    <li style={{display: windowWidth <= 980? '' : 'none', paddingLeft: '25px'}}><a class="submenus" href="/AboutUs/Login">Login</a></li> {/* This block of code was added */}

                <li><a href="/ContactUs">Contact Us</a>
                <ul  style={{display: windowWidth <= 980? 'none' : ''}}>
                    <li><a href="/JobSeekers/SendResume">Job Seekers</a></li>
                    <li><a href="/Employers/HireTalent">Employers</a></li>
                    <li><a href="/ContactUs/GeneralRequests">General Requests</a></li>
                </ul>
                </li>
                 {/*NAV BAR EXPERIMENT */}
                 <li style={{display: windowWidth <= 980? '' : 'none', paddingLeft: '25px'}} ><a class="submenus" href="/JobSeekers/SendResume">Job Seekers</a></li> 
                    <li  style={{display: windowWidth <= 980? '' : 'none', paddingLeft: '25px'}}><a class="submenus" href="/Employers/HireTalent">Employers</a></li>
                    <li style={{display: windowWidth <= 980? '' : 'none', paddingLeft: '25px'}}><a class="submenus"  href="/ContactUs/GeneralRequests">General Requests</a></li>


                </div>

                {/*NEW CODE------------------------------------------------------------------------------------------------------ */}
        

            </div>
        </nav>
    );
}

export default Nav;