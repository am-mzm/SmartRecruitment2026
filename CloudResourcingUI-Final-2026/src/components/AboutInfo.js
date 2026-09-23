import "./layout.css";
import butterfly from "./PaperButterfly.png";
import plants from "./Plants.png";
import services from "./Tools.png";
import utensils from "./Utensils.png";

function AboutInfo() {
    return (
        <>
        <div class="nav-text-phone">
    <p>{'<'}</p>
    <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
    </div>
        <div class="nav-text">
            <p onClick={() => window.location.href = "/"}  class="Page1-descr">Home</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/AboutUs"}  class="Page1-descr"> About Us</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/AboutUs/WhoWeAre"}  class="Page1-descr"> Who We Are</p>
        </div>






        <div class="dummy7 AV-container">
            <div class="dummy8 light-img2">
<img src={butterfly} class="dummy9" alt="Our mission: unlocking unique talent."/>
</div>
                <h1 class="AV-light-head dummy10" >Our mission: unlocking unique talent.</h1>
                <div class="light-img-and-desc-container">
                    
                    <div class="AV-values dummy11">
                        <p class="AV-light-desc">Cloud Resourcing believe that in today's knowledge economy each individual 
                has unique strength and talent, and we need to find the right match by helping 
                these individuals secure rewarding jobs and stay relevant in the ever-changing 
                world of work.  </p>
                    </div>
                    <img class="light-img dummy12" src={butterfly} alt="Our mission: unlocking unique talent."/>
                </div>
    </div>


    <div class="JS-container addedstyling1 JS-light-container">
    <div class="addedstyling2 light-img2">
<img src={plants} class="addedstyling3" alt="Our mission: unlocking unique talent."/>
</div>
<h1 class="JS-head JS-light-head">Our pledge: your complete corporate partner.</h1>
        <div class="light-img-and-desc-container">
            <img class="light-img addedstyling4" src={plants} alt="Our mission: unlocking unique talent."/>
            <div class="addedstyling5">
                <p class="JS-desc JS-light-desc">
                    For our clients, Cloud Resourcing is a one-stop-solution provider for all your 
                    corporate requirements. We nurture you with assistance to help you elevate from 
                    average to ace and win your trust by providing incomparable quality and unmatched services.
                </p>
            </div>
        </div>
    </div>

    <div class="AV-container addedstyling6">
        <div class="light-img2 addedstyling2">
            <img class="addedstyling7" src={services} alt="Our mission: unlocking unique talent."/>
        </div>
        <h1 class="AV-light-head addedstyling8">Our expertise: served with class.</h1>
        <div class="light-img-and-desc-container">
            <div class="AV-values addedstyling9">
                <p class="AV-light-desc"> 
                    Driven by quality we leave no stone unturned to deliver excellence. That is why our business 
                    operation today includes: 
                </p>
                <ul class="AV-light-desc AI-bullet-points-list addedstyling10">
                    <li>Value addition to client service</li>
                    <li>Assistance of seasoned IT professionals</li>
                    <li>Consultants on demand</li>
                    <li>Extraordinary quality</li>
                    <li>Conducive environment for staff</li>
                </ul>
            </div>
            <img class="light-img addedstyling11" src={services} alt="Our mission: unlocking unique talent."/>
        </div>
    </div>

    <div class="JS-container JS-light-container addedstyling6">
        <div class="light-img2 addedstyling2">
            <img class="addedstyling12" src={utensils} alt="Our mission: unlocking unique talent."/>
        </div>
        <h1 class="JS-head JS-light-head">Our cornerstone: talent and commitment</h1>
        <div class="light-img-and-desc-container">
            <img class="light-img addedstyling4" src={utensils} alt="Our mission: unlocking unique talent."/>
            <div class="addedstyling5">
                <p class="JS-desc JS-light-desc"> 
                    The best of talents converges all their efforts at Cloud Resourcing to make it a place of making 
                    promises and keeping them. While our impact will depend, to a large extent, on the role 
                    permitted for us, our commitment to the cause of our clients is steady and firm; our holistic 
                    discipline enables conception and implementation of optimal solutions that are aligned with the
                    clients’ business and technology strategies. 
                </p>
            </div>
        </div>
    </div>

    <div class="AV-cont addedstyling6">
        <h1 class="light-head AV-work">We want to work with you.</h1>
        <button onClick={() => window.location.href = "/ContactUs"} class="JS-button addedstyling13">Contact Us</button>
    </div>

    <div class="AV-cont addedstyling14">
        <button onClick={() => window.location.href = "/JobSeekers/WorkForUs"} class="JS-button JS-light-button addedstyling15">Learn More</button>
        <h1 class="dark-head AV-head">Join us today.</h1>
    </div>

        </>
    );
}

export default AboutInfo;