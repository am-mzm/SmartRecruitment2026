
import "./layout.css";
import quality from "./Quality.jpeg";
import clientf from "./ClientFocus.webp";
import integrity from "./Integrity.jpeg";
import collaboration from "./Collaboration.jpeg";
import innovation from "./Innovation.jpeg";
import commitment from "./Commitment.jpeg";


function AboutValues() {
    return (
        <>
        <div class="nav-text-phone">
    <p>{'<'}</p>
    <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
    </div>

            <div class="nav-text">
            <p onClick={() => window.location.href = "/"}  class="Page1-descr">Home </p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/AboutUs"}  class="Page1-descr"> About Us</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/AboutUs/OurValues"}  class="Page1-descr"> Our Values</p>
            </div>


            <div class="AV-container addedstyling21">
    <h1 class="AV-light-head">Our values.</h1>
    <div class="AV-values">
        <p class="AV-light-desc">
            Our values are more than just words on a page or mere marketing rhetoric. 
            They embody our approach in conducting business.
        </p>
    </div>
</div>

<div class="AV-img-container addedstyling22">
    <div>
        <div class="img__wrap">
            <img class="img__img" src={quality} alt="rocks balanced on top of each other" />
            <div class="img__description">
                Our commitment to delivering unparalleled quality ensures we exceed expectations in every project.
            </div>
        </div>
        <p class="img__text">Quality.</p>
    </div>
    <div>
        <div class="img__wrap">
            <img class="img__img" src={clientf} alt="lone marble" />
            <div class="img__description">
                We prioritize our clients, tailoring solutions to meet their unique needs and goals.
            </div>
        </div>
        <p class="img__text">Client-Focus.</p>
    </div>
    <div>
        <div class="img__wrap">
            <img class="img__img" src={integrity} alt="sharp object amidst pebbles" />
            <div class="img__description">
                Integrity is at the core of our operations, ensuring trust and transparency in all our dealings.
            </div>
        </div>
        <p class="img__text">Integrity.</p>
    </div>
</div>

<div class="AV-img-container addedstyling22">
    <div>
        <div class="img__wrap">
            <img class="img__img" src={innovation} alt="rocks balanced on top of each other" />
            <div class="img__description">
                Innovation drives us to continuously improve and deliver cutting-edge solutions.
            </div>
        </div>
        <p class="img__text">Innovation.</p>
    </div>
    <div>
        <div class="img__wrap">
            <img class="img__img" src={collaboration} alt="lone marble" />
            <div class="img__description">
                Collaboration fosters teamwork and synergies that achieve exceptional outcomes.
            </div>
        </div>
        <p class="img__text">Collaboration.</p>
    </div>
    <div>
        <div class="img__wrap">
            <img class="img__img" src={commitment} alt="sharp object amidst pebbles" />
            <div class="img__description">
                Our unwavering commitment ensures we deliver on our promises and exceed expectations.
            </div>
        </div>
        <p class="img__text">Commitment.</p>
    </div>
</div>

<div class="AV-cont addedstyling28">
    <h1 class="light-head AV-work addedstyling26">We want to work with you.</h1>
    <button onClick={() => window.location.href = "/ContactUs"} class="JS-button AV-button-contact2 addedstyling27">Contact Us</button>
</div>

<h1 class="dark-head AV-head">Join us today.</h1>

<div class="dark-div addedstyling29">
    <button onClick={() => window.location.href = "/JobSeekers/WorkForUs" } class="JS-button JS-light-button addedstyling30">Learn More</button>
    <p class="dark-desc AV-desc">
        Cloud Resourcing believes in unlocking individual strengths in today's knowledge economy, 
        providing comprehensive solutions for corporate needs. Our commitment to excellence drives 
        us to deliver unparalleled quality, with a focus on client service, seasoned professionals, 
        and a supportive environment. We promise to deliver and maintain unwavering commitment to 
        our clients' success, aligning solutions with their business strategies for optimal results.
    </p>
</div>

        </>
    );
}

export default AboutValues;