import "./layout.css";
import marble from "./Candles.png";

function Page2() {
    return (
        <>
        <div class="nav-text-phone">
    <p>{'<'}</p>
    <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
    </div>
            <div class="nav-text">
            <p onClick={() => window.location.href = "/"}  class="Page1-descr">Home</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/AboutUs"}  class="Page1-descr"> About Us </p>
            </div>


            <div class="JS-container JS-light-container">
    <h1 class="JS-head dummy-class-1 JS-light-head">Who we are.</h1>
            <div class="JS-div">
            
                <p class="JS-desc dummy-class-1 JS-light-desc">Cloud Resourcing believes in unlocking individual strengths in today's knowledge economy, 
                    providing comprehensive solutions for corporate needs. Our commitment to excellence drives 
                    us to deliver unparalleled quality, with a focus on client service, seasoned professionals, 
                    and a supportive environment. We promise to deliver and maintain unwavering commitment to 
                    our clients' success, aligning solutions with their business strategies for optimal results.</p>
        <button onClick={() => window.location.href = "/AboutUs/WhoWeAre"} class="JS-button dummy-class-2 JS-light-button">Learn More</button>
            </div>
    </div>

            <div class="dummy-class-3 light-container">
            <div style={{display: 'none'}} class="light-img2">
<img class="dummy4" src={marble} alt="many black balls together"/>
</div>

                <h1 class="light-head">Our values.</h1>
                <div class="light-img-and-desc-container">
                    <img class="light-img" src={marble} alt="marble"/>
                    <div class="dummy5">
                        <p class="light-desc">We have 6 core values which guide our every action and decision: Quality, Client-Focus, 
                            Collaboration, Commitment, Innovation, and Integrity.</p>
                        <button onClick={() => window.location.href = "/AboutUs/OurValues"} class="JS-button dummy6">Learn More</button>
                    </div>
                </div>
            </div>

            <div class="dummy-class-3 JS-container JS-light-container">
    <h1 class="JS-head dummy-class-1 JS-light-head">Visit us.</h1>
            <div class="JS-div">
            
                <p class="JS-desc dummy-class-1 JS-light-desc">We're dedicated to supporting you with all your needs. Please don't hesitate to drop by any of our office locations for assistance.</p>
        <button onClick={() => window.location.href = "/AboutUs/OfficeLocations"} class="JS-button dummy-class-2 JS-light-button">Find a Location</button>
            </div>
    </div>
        </>
    );
}

export default Page2;