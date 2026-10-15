import ContactFormHT from "./ContactFormHT";
import chess from './Chess.png';

function HireTalent() {
  return (
    <>
    <div class="nav-text-phone">
    <p>{'<'}</p>
    <p onClick={() => window.location.href = "/"} class="Page1-descr">Home</p>
    </div>
    <div class="nav-text">
            <p onClick={() => window.location.href = "/"}  class="Page1-descr">Home</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/Employers"}  class="Page1-descr"> Employers</p>
            <p>{'>'}</p>
            <p onClick={() => window.location.href = "/Employers/HireTalent"}  class="Page1-descr"> Hire Talent</p>
    </div>


    <div class="AV-container addedstyling60">
    <div class="light-img2 addedstyling61">
        <img class="addedstyling62" src={chess} alt="many black balls together"/>
    </div>
    <h1 class="AV-light-head addedstyling63">Allow us to assist you in discovering your next valuable team member.</h1>
    <div class="light-img-and-desc-container">
        <div class="AV-values addedstyling64">
            <p class="AV-light-desc">Whether your company requires temporary or permanent talent, our 
            consultants are poised to find the ideal match for your needs.</p>
        </div>
        <img class="light-img addedstyling65" src={chess} alt="many black balls together"/>
    </div>
</div>

<div class="JS-container JS-light-container addedstyling60">
    <h1 class="JS-head JS-light-head addedstyling66">A member of our team will reach out to you shortly.</h1>
</div>
<ContactFormHT class="SeekerResume-ContactForm"/>

    </>
  );
}

export default HireTalent;