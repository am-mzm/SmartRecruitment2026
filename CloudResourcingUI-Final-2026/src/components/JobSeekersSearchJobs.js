import React, { useEffect } from 'react';

function YourComponent() {
    useEffect(() => {
        // Create a script element
        const script = document.createElement('script');
        // Set the source and any attributes as needed
        script.src = 'https://jobsapi.ceipal.com/APISource/widget.js';
        script.setAttribute('data-ceipal-api-key', 'a2dsNkp0dkpONzFTS2ZEd1JEUEw0QT09');
        // Append the script to the body
        document.body.appendChild(script);

        // Cleanup: Remove the script when the component unmounts
        return () => {
            document.body.removeChild(script);
        };
    }, []); // Empty dependency array ensures this runs only once on mount

    return (
        <div id="example-widget-container"></div>
    );
}

export default YourComponent;