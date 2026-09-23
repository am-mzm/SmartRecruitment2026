import "./layout.css";
import React from "react";
import resume from "./GirlWorkingOnLaptop.jpg"
import leafPhone from "./LeafBorderPhone.png";
import girl from "./ManWorking.jpg";
import laugh from "./ManShakingHand.webp";
import paper from "./AbstractWhitePaper.png";
import leaf from "./LeafBorder.png";
import logo from "./GoodCloudResourcingLogo.png";

function Page1() {
    return (
        <>
         
        {/*
        <div class="job-search">
         <input type="text" placeholder="Job Title/Keyword" class="search-job" />
         <select class="search-job">
          <option value="">Location</option>
          <option value="location1">Location 1</option>
          <option value="location2">Location 2</option>
          <option value="location3">Location 3</option>
         </select>
         <select class="search-job">
          <option value="">Industry</option>
          <option value="location1">Industry 1</option>
          <option value="location2">Industry 2</option>
          <option value="location3">Industry 3</option>
         </select>
         <select class="search-job">
          <option value="">Type</option>
          <option value="location1">Remote</option>
          <option value="location2">Hybrid</option>
          <option value="location3">In Person</option>
         </select>
         <select class="search-job">
          <option value="">Status</option>
          <option value="location1">Active</option>
          <option value="location2">Submitted</option>
         </select>
         <button class="search-job button-job">Search # Jobs</button>
         <button class="search-job button-adv">Advanced Search</button>
     </div>
        */}
     
     
    

{/*
        <h1 class="discover-jobs-text">Discover jobs in your field.</h1>
        <div class="columns">
            <div class="column-1">
                <button>Arts</button>
                <button>Aviation</button>
                <button>Computer Hardware</button>
                <button>Computer Software</button>
            </div>
            <div class="column-2">
                <button>Consulting</button>
                <button>Electronics</button>
                <button>Entertainment</button>
                <button>Healthcare</button>
            </div>
            <div class="column-3">
                <div class="column-3-1">
                <button>Healthcare</button>
                <button>Public Relations</button>
                </div>
                <div class="column-3-2">
                <button>Retail</button>
                <button>All Jobs</button>
                </div>
            </div>
        </div>

*/}

<div class="addedstyling75 animation">
    <div class="container-animation">
        <div class="animation-wrapper">
            <img src={logo} alt="Logo" class="logo-animation addedstyling76" />
            <span class="company-name-animation">CloudResourcing</span>
        </div>
        <div class="slogan-wrapper addedstyling77">
            <span class="slogan">Elevating you to your true potential.</span>
        </div>
        <div class="addedstyling78 leaf-desktop">
            <img src={leaf} alt="leaf" class="slogan img-animation addedstyling79" />
        </div>
        <div class="addedstyling78 leaf-phone">
            <img src={leafPhone} alt="leaf" class="slogan img-animation addedstyling79" />
        </div>
    </div>
</div>
<h1 class="opportunity-text">Opportunity knocks; answer the door.</h1>
<div class="addedstyling80">
    <button onClick={() => window.location.href = "/JobSeekers/SearchJobs"} class="search-job-button addedstyling81">Search Jobs</button>
</div>
<div class="next-step">
    <h1 class="step-text">Take the next step in your career journey.</h1>
    <div class="img-container">
        <div class="addedstyling82">
            <img onClick={() => window.location.href = "/JobSeekers/SearchJobs"} class="img-resume" src={laugh} alt="girl working on her laptop"/>
            <p class="Page1-descr" onClick={() => window.location.href = "/JobSeekers/SearchJobs"}>Find a job that suits you.</p>
        </div>
        <div class="addedstyling83">
            <img onClick={() => window.location.href = "/JobSeekers/WorkForUs"} class="img-resume" src={resume} alt="girl laughing at work"/>
            <p onClick={() => window.location.href = "/JobSeekers/WorkForUs"} class="Page1-descr">Join us.</p>
        </div>
        <div class="addedstyling84">
            <img onClick={() => window.location.href = "/JobSeekers/SendResume"} class="img-resume" src={girl} alt="laptop image"/>
            <p onClick={() => window.location.href = "/JobSeekers/SendResume"} class="Page1-descr">Uncertain about suitable jobs? upload your resume.</p>
        </div>
    </div>
</div>
<h1 class="story-text addedstyling85">Discover the story behind our mission.</h1>
<div class="story-content">
    <div class="storey-left addedstyling86">
        <p>Cloud Resourcing is dedicated to matching individuals with their ideal careers in today's dynamic knowledge economy. We're your ultimate solution for corporate needs, elevating businesses from average to outstanding with top-notch services and expert assistance. Committed to quality and excellence, our team ensures unmatched value addition, staff support, and tailored solutions that align perfectly with our clients' business and tech strategies. Join us at Cloud Resourcing, where promises are made and kept.</p>
        <button onClick={() => window.location.href = "/AboutUs"} class="JS-button JS-light-button addedstyling87">Learn More!</button>
    </div>
    <div class="story-side">
        <img class="dummy77" src={paper} alt="abstract paper drawing"/>
    </div>
</div>
<div class="talent-content addedstyling88">
    <h1 class="talent-text">Seeking top talent to hire? Look no further.</h1>
    <div class="talent-container addedstyling89">
        <button onClick={() => window.location.href = "/Employers/HireTalent"} class="talent-button addedstyling90">Hire Talent!</button>
        <p class="talent-desc-text">Join the pool of job postings across a multitude of industries, offering an unparalleled opportunity to connect with top-notch candidates for your position. From technology and finance to beyond, our platform caters to diverse talents and specialties. Join us in the quest for excellence as we strive to match your needs with the perfect candidate.</p>
    </div>
</div>
<div class="JS-container JS-light-container addedstyling91">
    <h1 class="JS-head JS-light-head addedstyling92">Prefer meeting in person? no problem.</h1>
    <div class="JS-div">
        <p class="JS-desc JS-light-desc addedstyling93">Click the button to find a nearby location and meet us in person. Your convenience is our priority.</p>
        <button onClick={() => window.location.href = "/AboutUs/OfficeLocations"} class="JS-button JS-light-button">Find a Location</button>
    </div>
</div>


        </>
    );
}

export default Page1;