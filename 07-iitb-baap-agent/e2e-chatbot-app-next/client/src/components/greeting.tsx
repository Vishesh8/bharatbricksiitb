import { motion } from 'framer-motion';
import iitbLogo from '@/assets/iitb-logo.png';

export const Greeting = () => {
  return (
    <div
      key="overview"
      className="mx-auto flex size-full max-w-3xl flex-col justify-center px-4 mb-6"
    >
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 10 }}
        className="flex flex-col items-center gap-4"
      >
        <img src={iitbLogo} alt="IIT Bombay" className="h-16 w-16 md:h-20 md:w-20 rounded-lg" />
        <div className="font-semibold text-lg md:text-xl text-center">
          Namaste, junta! Welcome to IITB Campus Advisor
        </div>
        <div className="text-sm text-muted-foreground text-center max-w-md">
          Your AI guide to IIT Bombay campus life — powered by real student
          discussions from r/iitbombay and campus analytics.
        </div>
      </motion.div>
    </div>
  );
};
