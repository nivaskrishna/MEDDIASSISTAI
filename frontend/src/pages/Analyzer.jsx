import React from "react";
import AnalyzerChat from "../components/Chat/AnalyzerChat";

const Analyzer = (props) => {
  return (
    <div className="py-2 px-1">
      <AnalyzerChat {...props} />
    </div>
  );
};

export default Analyzer;
