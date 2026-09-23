import virus from './Lightbulb.png';
import pot from "./PlantsInPot.png";

function JobSeekers() {
  return (
    <>
    
    <div class="nav-text-phone">
    <p>{'<'}</p>
    <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
    </div>
    <div class="nav-text">
            <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/JobSeekers/"} class="Page1-descr"> Job Seekers</p>
        </div>
        <div class="addedstyling94 JS-container">
    <h1 class="JS-head">Let us open doors for you.</h1>
    <div class="JS-div">
        <p class="JS-desc">Ready to discover your next career move? Click the button to explore the latest job opportunities on our website. Take the next step towards your professional journey today.</p>
        <button onClick={() => window.location.href = "/JobSeekers/SearchJobs"} class="JS-button">Explore Jobs</button>
    </div>
</div>

<div class="JS-container JS-light-container">
    <div class="light-img2 addedstyling95">
        <img class="addedstyling96" src={virus} alt="many black balls together"/>
    </div>
    <h1 class="JS-head JS-light-head">Our values.</h1>
    <div class="light-img-and-desc-container">
        <img class="addedstyling97 light-img" src={virus} alt="many black balls together"/>
        <div class="addedstyling98">
            <p class="JS-desc JS-light-desc">We have 6 core values which guide our every action and decision: Quality, Client-Focus, Collaboration, Commitment, Innovation, and Integrity.</p>
            <button onClick={() => window.location.href = "/AboutUs/OurValues"} class="addedstyling99 JS-button JS-light-button">Learn More</button>
        </div>
    </div>
</div>

<div class="addedstyling100 JS-container">
    <h1 class="JS-head">Discover a career that ignites your passion.</h1>
    <div class="JS-div">
        <p class="JS-desc">Feeling uncertain about which career path suits you best? Simply upload your resume below, and let us connect you with a specialized recruiter in your field. They'll leverage your unique skills and experience to pinpoint job opportunities tailored to your preferences, ensuring you find the perfect fit for your next career move.</p>
        <button onClick={() => window.location.href = "/JobSeekers/SendResume"} class="JS-button">Upload Now</button>
    </div>
</div>

<div class="addedstyling101 JS-container JS-light-container">
    <div class="light-img2 addedstyling102">
        <img class="addedstyling103" src={pot} alt="many black balls together"/>
    </div>
    <h1 class="JS-head JS-light-head">Prefer meeting in person? no problem.</h1>
    <div class="light-img-and-desc-container">
        <img class="addedstyling104 light-img" src={pot} alt="many black balls together"/>
        <div class="addedstyling105">
            <p class="JS-desc JS-light-desc">Click the button to find a nearby location and meet us in person. Your convenience is our priority.</p>
            <button onClick={() => window.location.href = "/AboutUs/OfficeLocations"} class="addedstyling106 JS-button JS-light-button">Find a Location</button>
        </div>
    </div>
</div>



        

        
    </>
  );
}

export default JobSeekers;