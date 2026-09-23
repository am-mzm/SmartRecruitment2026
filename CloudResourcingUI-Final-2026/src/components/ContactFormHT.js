import { useRef, useState } from 'react';
import emailjs from '@emailjs/browser';
import "./layout.css";

/* CONTACT FORM FOR THE EMPLOYERS - HIRE TALENT PAGE */

function ContactForm() {
        const form = useRef();
        const [message, setMessage] = useState('');
        const [charCount, setCharCount] = useState(0);
        const [mobileNumber, setMobileNumber] = useState('');
  
        const handleInputChange = (event) => {
          const { value } = event.target;
          if (/^[0-9+\-()]*$/.test(value)) {
            setMobileNumber(value);
          }
        };

      
        const sendEmail = (e) => {
          e.preventDefault();
          const emailInput = document.getElementsByName('email')[0].value;

    const validateEmail = (email) => {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(email);
    };
  

      if (!validateEmail(emailInput)) {
        alert('Please enter a valid email address.');
      }

      
    emailjs
    .sendForm('service_0ltuu5k', 'template_tvytzba', form.current, {
      publicKey: 'MklEzlSFxIItnkxOM',
    })
    .then(
      () => {
        console.log('SUCCESS!');
        form.current.reset();
        setMessage('');
        setCharCount(0);
        setMobileNumber('');
        alert("Email sent successfully.");
      },
      (error) => {
        console.log('FAILED...', error.text);
        alert('Failed to send email. Please try again later.');
      },
    );
      
    


  
      

        };
        const handleMessageChange = (e) => {
          setMessage(e.target.value);
          setCharCount(e.target.value.length);
        };
      
      
  return (
    <form ref={form} onSubmit={sendEmail} class="SeekerResumeContactForm">
       <input class="input" type="text" name="form_location" value="Hire Talent Request" className='addedstyling46'  placeholder="first name..." />
      <label>First Name*</label>
      <input maxLength="150" type="text" name="first_name" required placeholder="first name..." />
      <label>Last Name*</label>
      <input maxLength="150" type="text" required name="last_name" placeholder="last name..." />
      <label>Contact Number*</label>
      <input maxLength="20" type="tel" 
      required  
      name="contact_number" 
      placeholder="number..."
      value={mobileNumber}
      onChange={handleInputChange}
      />
      <label>Email*</label>
      <input maxLength="150" type="email" required name="email" placeholder="email..." />
      <label>Postal Code</label>
      <input maxLength="30" type="text" name="postal_code" placeholder="postal code..." />
      <label>Company Name*</label>
      <input maxLength="200" required type="text" name="company" placeholder="company..." />

      <label>How can we help you?</label>
      <textarea
        name="message"
        placeholder="enter details here..."
        maxLength="500"
        value={message}
        onChange={handleMessageChange}
        className='addedstyling44'
      />
      <p className='addedstyling45'>{charCount}/500 characters</p>
      <input type="submit" value="Send" class="SeekerResume-send-button"/>
    </form>
  );
};

export default ContactForm; 
