import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, SkipForward } from 'lucide-react';
import { FollowUpQuestion } from '../types';

interface FollowUpQuestionsProps {
  questions: FollowUpQuestion[];
  originalQuery: string;
  onSubmit: (answers: Record<string, string>) => void;
  onSkip: () => void;
}

export function FollowUpQuestions({
  questions,
  originalQuery,
  onSubmit,
  onSkip,
}: FollowUpQuestionsProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [textInputs, setTextInputs] = useState<Record<string, string>>({});

  const handleOptionSelect = (questionId: string, optionLabel: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionLabel,
    }));
  };

  const handleTextChange = (questionId: string, value: string) => {
    setTextInputs((prev) => ({
      ...prev,
      [questionId]: value,
    }));
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value,
    }));
  };

  const handleSubmit = () => {
    // Filter out empty answers
    const validAnswers = Object.fromEntries(
      Object.entries(answers).filter(([_, v]) => v.trim().length > 0)
    );
    onSubmit(validAnswers);
  };

  const answeredCount = Object.values(answers).filter((v) => v.trim().length > 0).length;
  const canSubmit = answeredCount > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="w-full max-w-[680px] mx-auto"
    >
      {/* Query context */}
      <div className="mb-6 text-center">
        <p className="text-sm text-muted-foreground mb-1">Searching for:</p>
        <p className="text-lg font-medium text-foreground">"{originalQuery}"</p>
      </div>

      {/* Questions card */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
        <h2 className="text-lg font-semibold text-foreground mb-1">
          Help me find better matches
        </h2>
        <p className="text-sm text-muted-foreground mb-6">
          Answer a few questions to narrow down the search results.
        </p>

        <div className="space-y-6">
          {questions.map((question, idx) => (
            <motion.div
              key={question.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="space-y-3"
            >
              <label className="text-sm font-medium text-foreground">
                {question.question}
              </label>

              {question.type === 'text' ? (
                <input
                  type="text"
                  value={textInputs[question.id] || ''}
                  onChange={(e) => handleTextChange(question.id, e.target.value)}
                  placeholder="Type your answer..."
                  className="w-full bg-gray-50 rounded-lg px-4 py-3 text-sm placeholder:text-muted-foreground/50 outline-none focus:ring-2 focus:ring-indigo-300 border border-gray-200"
                />
              ) : (
                <div className="flex flex-wrap gap-2">
                  {question.options.map((option) => {
                    const isSelected = answers[question.id] === option.label;
                    return (
                      <button
                        key={option.id}
                        onClick={() => handleOptionSelect(question.id, option.label)}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                          isSelected
                            ? 'bg-indigo-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {option.label}
                      </button>
                    );
                  })}
                </div>
              )}
            </motion.div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-100">
          <button
            onClick={onSkip}
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <SkipForward size={14} />
            Skip and search anyway
          </button>

          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-full text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Continue
            <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
