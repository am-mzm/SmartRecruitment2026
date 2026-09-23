import { useRef, useState } from 'react';
import emailjs from '@emailjs/browser';
import "./layout.css";

/* CONTACT FORM FOR THE CONTACT US - GENERAL REQUESTS PAGE */

function ContactFormGT() {
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
<form onSubmit={sendEmail}  ref={form} class="SeekerResumeContactForm">
<input class="input" type="text" name="form_location" value="General Request" className="addedstyling46" placeholder="first name..." />
  <label>First Name*</label>
  <input maxLength="150" type="text" name="first_name" required placeholder="first name..." />
  <label>Last Name*</label>
  <input maxLength="150" type="text" name="last_name"  required placeholder="last name..." />
  <label>Contact Number*</label>
  <input maxLength="20" required value={mobileNumber}
      onChange={handleInputChange} type="tel" name="contact_number" placeholder="number..." />
  <label>Email*</label>
  <input maxLength="150" type="email" name="email" required placeholder="email..." />
  <label>How can we help you?*</label>
      <textarea
        name="message"
        placeholder="enter details here..."
        maxLength="500"
        value={message}
        onChange={handleMessageChange}
        required
        className='addedstyling44'
      />
      <p className='addedstyling45'>{charCount}/500 characters</p>
  <input type="submit" value="Send" required class="SeekerResume-send-button"/>
</form>
);
}

export default ContactFormGT;