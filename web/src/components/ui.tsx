import React from "react";

export const Card = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <div className={`bg-white border border-gray-300 rounded-sm mb-4 ${className}`}>
        {children}
    </div>
);

export const CardHeader = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <div className={`px-4 py-3 border-b border-gray-200 bg-gray-50 flex justify-between items-center ${className}`}>
        {children}
    </div>
);

export const CardBody = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <div className={`p-4 ${className}`}>
        {children}
    </div>
);

export const Label = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <label className={`block text-xs font-semibold text-gray-600 mb-1 ${className}`}>
        {children}
    </label>
);

export const Select = (props: React.SelectHTMLAttributes<HTMLSelectElement>) => (
    <select {...props} className="block w-full text-sm border-gray-300 rounded shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 h-8">
        {props.children}
    </select>
);

export const Input = (props: React.InputHTMLAttributes<HTMLInputElement>) => (
    <input {...props} className="block w-full text-sm border-gray-300 rounded shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 h-8 px-2" />
);

export const Checkbox = ({ label, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { label?: string }) => (
    <label className="inline-flex items-center">
        <input type="checkbox" {...props} className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" />
        {label && <span className="ml-2 text-sm text-gray-700">{label}</span>}
    </label>
);
