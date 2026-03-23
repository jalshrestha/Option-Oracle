"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  BookOpen,
  GraduationCap,
  PlayCircle,
  Trophy,
  Search,
  Clock,
  ChevronRight,
  Star,
  TrendingUp,
  Zap,
  Lock,
  CheckCircle,
  Target,
  Brain,
  BarChart3,
} from "lucide-react";

// Mock course data
const courses = [
  {
    id: 1,
    title: "Options Trading Fundamentals",
    description: "Master the basics of options trading, from calls and puts to understanding option pricing.",
    level: "Beginner",
    duration: "2h 30m",
    lessons: 12,
    completedLessons: 12,
    progress: 100,
    image: "/course-fundamentals.jpg",
    category: "basics",
    rating: 4.9,
    enrolled: 15420,
    instructor: "Option Oracle AI",
  },
  {
    id: 2,
    title: "The Greeks Explained",
    description: "Deep dive into Delta, Gamma, Theta, Vega, and how they affect your options positions.",
    level: "Intermediate",
    duration: "3h 15m",
    lessons: 18,
    completedLessons: 14,
    progress: 78,
    image: "/course-greeks.jpg",
    category: "intermediate",
    rating: 4.8,
    enrolled: 8956,
    instructor: "Option Oracle AI",
  },
  {
    id: 3,
    title: "Advanced Spread Strategies",
    description: "Learn complex multi-leg strategies including iron condors, butterflies, and calendar spreads.",
    level: "Advanced",
    duration: "4h 45m",
    lessons: 24,
    completedLessons: 6,
    progress: 25,
    image: "/course-spreads.jpg",
    category: "advanced",
    rating: 4.9,
    enrolled: 5678,
    instructor: "Option Oracle AI",
  },
  {
    id: 4,
    title: "Technical Analysis for Options",
    description: "Combine technical analysis with options trading for better entry and exit timing.",
    level: "Intermediate",
    duration: "3h 30m",
    lessons: 20,
    completedLessons: 0,
    progress: 0,
    image: "/course-ta.jpg",
    category: "intermediate",
    rating: 4.7,
    enrolled: 7234,
    instructor: "Option Oracle AI",
  },
  {
    id: 5,
    title: "Risk Management Masterclass",
    description: "Protect your portfolio with advanced risk management techniques and position sizing.",
    level: "Advanced",
    duration: "2h 45m",
    lessons: 15,
    completedLessons: 0,
    progress: 0,
    image: "/course-risk.jpg",
    category: "advanced",
    rating: 4.9,
    enrolled: 4567,
    instructor: "Option Oracle AI",
    locked: true,
  },
  {
    id: 6,
    title: "Earnings Plays",
    description: "Strategies for trading options around earnings announcements and volatility events.",
    level: "Advanced",
    duration: "2h 15m",
    lessons: 14,
    completedLessons: 0,
    progress: 0,
    image: "/course-earnings.jpg",
    category: "advanced",
    rating: 4.8,
    enrolled: 6789,
    instructor: "Option Oracle AI",
    locked: true,
  },
];

const glossaryTerms = [
  { term: "Call Option", definition: "A contract giving the buyer the right, but not the obligation, to buy an asset at a specified price within a specific time period." },
  { term: "Put Option", definition: "A contract giving the buyer the right, but not the obligation, to sell an asset at a specified price within a specific time period." },
  { term: "Strike Price", definition: "The price at which the option holder can buy (call) or sell (put) the underlying asset." },
  { term: "Premium", definition: "The price paid by the buyer to the seller for an option contract." },
  { term: "Delta", definition: "Measures the rate of change of the option price with respect to changes in the underlying asset's price." },
  { term: "Gamma", definition: "Measures the rate of change in delta over time as the underlying price changes." },
  { term: "Theta", definition: "Measures the rate of time decay of an option's value." },
  { term: "Vega", definition: "Measures sensitivity to volatility changes in the underlying asset." },
  { term: "Implied Volatility", definition: "The market's forecast of likely movement in the underlying asset's price." },
  { term: "In The Money (ITM)", definition: "When an option has intrinsic value - calls with strike below current price, puts with strike above." },
  { term: "At The Money (ATM)", definition: "When an option's strike price equals the current price of the underlying asset." },
  { term: "Out of The Money (OTM)", definition: "When an option has no intrinsic value - calls with strike above current price, puts with strike below." },
];

const achievements = [
  { id: 1, name: "First Steps", description: "Complete your first lesson", icon: Star, earned: true },
  { id: 2, name: "Knowledge Seeker", description: "Complete 10 lessons", icon: BookOpen, earned: true },
  { id: 3, name: "Greek Scholar", description: "Master the Greeks course", icon: Brain, earned: true },
  { id: 4, name: "Risk Manager", description: "Complete Risk Management", icon: Target, earned: false },
  { id: 5, name: "Strategy Master", description: "Complete all strategy courses", icon: BarChart3, earned: false },
  { id: 6, name: "Options Expert", description: "Complete all courses", icon: Trophy, earned: false },
];

export default function LearnPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");

  const filteredCourses = courses.filter((course) => {
    const matchesSearch = course.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "all" || course.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const totalProgress = Math.round(
    courses.reduce((sum, c) => sum + c.progress, 0) / courses.length
  );

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Learning Center</h1>
          <p className="text-muted-foreground">
            Master options trading with AI-powered courses
          </p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="flex items-center gap-1 px-3 py-1">
            <Trophy className="h-4 w-4 text-warning" />
            3 / 6 Achievements
          </Badge>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="border-accent/30 bg-gradient-to-br from-accent/10 to-transparent">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-accent/20 p-2">
                  <GraduationCap className="h-5 w-5 text-accent" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-muted-foreground">Overall Progress</p>
                  <p className="text-2xl font-bold">{totalProgress}%</p>
                  <Progress value={totalProgress} className="mt-2 h-2" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-muted p-2">
                  <BookOpen className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Courses Enrolled</p>
                  <p className="text-2xl font-bold">{courses.filter((c) => c.progress > 0).length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-muted p-2">
                  <CheckCircle className="h-5 w-5 text-success" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Lessons Completed</p>
                  <p className="text-2xl font-bold">
                    {courses.reduce((sum, c) => sum + c.completedLessons, 0)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="border-border/50 bg-card/50">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-muted p-2">
                  <Clock className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Hours Learned</p>
                  <p className="text-2xl font-bold">8.5</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <Tabs defaultValue="courses" className="space-y-6">
        <TabsList>
          <TabsTrigger value="courses" className="flex items-center gap-2">
            <PlayCircle className="h-4 w-4" />
            Courses
          </TabsTrigger>
          <TabsTrigger value="glossary" className="flex items-center gap-2">
            <BookOpen className="h-4 w-4" />
            Glossary
          </TabsTrigger>
          <TabsTrigger value="achievements" className="flex items-center gap-2">
            <Trophy className="h-4 w-4" />
            Achievements
          </TabsTrigger>
        </TabsList>

        <TabsContent value="courses" className="space-y-6">
          {/* Search and Filter */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-64">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search courses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex gap-2">
              {["all", "basics", "intermediate", "advanced"].map((category) => (
                <Button
                  key={category}
                  variant={selectedCategory === category ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedCategory(category)}
                  className={selectedCategory === category ? "bg-accent text-accent-foreground" : ""}
                >
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </Button>
              ))}
            </div>
          </div>

          {/* Continue Learning */}
          {courses.filter((c) => c.progress > 0 && c.progress < 100).length > 0 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Continue Learning</h2>
              <div className="grid gap-4 md:grid-cols-2">
                {courses
                  .filter((c) => c.progress > 0 && c.progress < 100)
                  .map((course, i) => (
                    <motion.div
                      key={course.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                    >
                      <Card className="border-accent/30 bg-gradient-to-br from-accent/5 to-transparent transition-all hover:border-accent/50">
                        <CardContent className="flex items-center gap-4 p-4">
                          <div className="flex h-16 w-16 items-center justify-center rounded-lg bg-accent/20">
                            <Zap className="h-8 w-8 text-accent" />
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold">{course.title}</h3>
                            <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
                              <span>{course.completedLessons}/{course.lessons} lessons</span>
                              <span>-</span>
                              <span>{course.duration}</span>
                            </div>
                            <Progress value={course.progress} className="mt-2 h-2" />
                          </div>
                          <Button className="bg-accent text-accent-foreground hover:bg-accent/90">
                            Continue
                            <ChevronRight className="ml-1 h-4 w-4" />
                          </Button>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
              </div>
            </div>
          )}

          {/* All Courses */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">All Courses</h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredCourses.map((course, i) => (
                <motion.div
                  key={course.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <Card className={`group h-full border-border/50 bg-card/50 transition-all hover:border-accent/50 ${course.locked ? "opacity-60" : ""}`}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-accent/10">
                          {course.locked ? (
                            <Lock className="h-6 w-6 text-muted-foreground" />
                          ) : course.progress === 100 ? (
                            <CheckCircle className="h-6 w-6 text-success" />
                          ) : (
                            <PlayCircle className="h-6 w-6 text-accent" />
                          )}
                        </div>
                        <Badge variant={
                          course.level === "Beginner" ? "default" :
                          course.level === "Intermediate" ? "secondary" : "outline"
                        }>
                          {course.level}
                        </Badge>
                      </div>
                      <CardTitle className="mt-4 text-lg">{course.title}</CardTitle>
                      <CardDescription>{course.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          {course.duration}
                        </span>
                        <span className="flex items-center gap-1">
                          <BookOpen className="h-4 w-4" />
                          {course.lessons} lessons
                        </span>
                        <span className="flex items-center gap-1">
                          <Star className="h-4 w-4 text-warning" />
                          {course.rating}
                        </span>
                      </div>
                      {course.progress > 0 && (
                        <div className="mt-3">
                          <div className="mb-1 flex justify-between text-xs">
                            <span>Progress</span>
                            <span>{course.progress}%</span>
                          </div>
                          <Progress value={course.progress} className="h-1.5" />
                        </div>
                      )}
                      <Button 
                        className="mt-4 w-full"
                        variant={course.locked ? "outline" : "default"}
                        disabled={course.locked}
                      >
                        {course.locked ? (
                          <>
                            <Lock className="mr-2 h-4 w-4" />
                            Locked
                          </>
                        ) : course.progress === 100 ? (
                          <>
                            <CheckCircle className="mr-2 h-4 w-4" />
                            Review
                          </>
                        ) : course.progress > 0 ? (
                          <>
                            <PlayCircle className="mr-2 h-4 w-4" />
                            Continue
                          </>
                        ) : (
                          <>
                            <PlayCircle className="mr-2 h-4 w-4" />
                            Start Course
                          </>
                        )}
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="glossary" className="space-y-4">
          <Card className="border-border/50 bg-card/50 backdrop-blur">
            <CardHeader>
              <CardTitle>Options Trading Glossary</CardTitle>
              <CardDescription>
                Essential terms every options trader should know
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {glossaryTerms.map((item, i) => (
                  <motion.div
                    key={item.term}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="rounded-lg border border-border/50 bg-background/50 p-4"
                  >
                    <h4 className="font-semibold text-accent">{item.term}</h4>
                    <p className="mt-1 text-sm text-muted-foreground">{item.definition}</p>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="achievements" className="space-y-4">
          <Card className="border-border/50 bg-card/50 backdrop-blur">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5 text-warning" />
                Your Achievements
              </CardTitle>
              <CardDescription>
                Track your learning milestones
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {achievements.map((achievement, i) => (
                  <motion.div
                    key={achievement.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.1 }}
                    className={`flex items-center gap-4 rounded-lg border p-4 ${
                      achievement.earned
                        ? "border-warning/30 bg-warning/5"
                        : "border-border/50 bg-background/50 opacity-60"
                    }`}
                  >
                    <div className={`rounded-full p-3 ${
                      achievement.earned ? "bg-warning/20" : "bg-muted"
                    }`}>
                      <achievement.icon className={`h-6 w-6 ${
                        achievement.earned ? "text-warning" : "text-muted-foreground"
                      }`} />
                    </div>
                    <div>
                      <h4 className="font-semibold">{achievement.name}</h4>
                      <p className="text-sm text-muted-foreground">{achievement.description}</p>
                    </div>
                    {achievement.earned && (
                      <CheckCircle className="ml-auto h-5 w-5 text-success" />
                    )}
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
