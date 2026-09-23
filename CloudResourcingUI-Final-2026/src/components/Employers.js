import paper from "./BlueFlower.png";

function Employers() {
    return (
        <>
        <div class="nav-text-phone">
    <p>{'<'}</p>
    <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
    </div>
        <div class="nav-text">
            <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/Employers"} class="Page1-descr"> Employers</p>
        </div>


        <div class="JS-container">
    <div class="light-img2 addedstyling55">
        <img class="addedstyling56" src={paper} alt="many black balls together"/>
    </div>
    <h1 class="JS-head addedstyling57">Why us?</h1>
    <div class="JS-div Emp-div">
        <p class="JS-desc Emp-div">Employers, partner with Cloud Resourcing for tailored 
        solutions that drive success. Our client-focused approach ensures your unique 
        needs are met, while our collaborative efforts deliver innovative solutions. 
        Experience seamless support and guaranteed results with us.</p>
        <div class="story-side Emp-div">
            <img class="Emp-img addedstyling58" src={paper} alt="abstract paper drawing"/>
        </div>
    </div>
</div>

<div class="JS-container JS-light-container addedstyling59">
    <h1 class="JS-head JS-light-head">Seeking top talent to hire? Look no further.</h1>
    <div class="JS-div JS-light-div">
        <button onClick={() => window.location.href = "/Employers/HireTalent"} class="JS-button JS-light-button">Apply Now</button>
        <p class="JS-desc JS-light-desc">Join the pool of job postings across a multitude of 
        industries, offering an unparalleled opportunity to connect with top-notch candidates 
        for your position. From technology and finance to beyond, our platform 
        caters to diverse talents and specialties. Join us in the quest for excellence as we 
        strive to match your needs with the perfect candidate.</p>
    </div>
</div>


        </>
    );
}

export default Employers;