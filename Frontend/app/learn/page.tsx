'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import {
  BookOpen,
  GraduationCap,
  PlayCircle,
  Trophy,
  Search,
  Clock,
  ChevronRight,
} from 'lucide-react'
import {
  useEducationContent,
  useGlossary,
  useLearningPath,
} from '@/lib/hooks/use-api'

export default function LearnPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all')
  const [glossarySearch, setGlossarySearch] = useState('')

  const { data: content, isLoading: contentLoading } = useEducationContent(
    selectedDifficulty !== 'all' ? { difficulty: selectedDifficulty.toUpperCase() } : undefined
  )
  const { data: glossaryTerms, isLoading: glossaryLoading } = useGlossary(
    glossarySearch || undefined
  )
  const { data: learningPath, isLoading: pathLoading } = useLearningPath()

  const filteredContent = (content || []).filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Learning Center</h1>
          <p className="text-muted-foreground">
            Master options trading with AI-powered courses
          </p>
        </div>
      </div>

      {/* Learning path overview */}
      {pathLoading ? (
        <Skeleton className="h-24 w-full" />
      ) : learningPath ? (
        <Card className="border-accent/30 bg-gradient-to-br from-accent/10 to-transparent">
          <CardContent className="flex flex-wrap items-center gap-6 p-4">
            <div className="flex items-center gap-3">
              <GraduationCap className="h-6 w-6 text-accent" />
              <div>
                <p className="text-sm text-muted-foreground">Current Level</p>
                <p className="text-lg font-bold capitalize">{learningPath.current_level}</p>
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Next Milestone</p>
              <p className="text-sm font-medium">{learningPath.next_milestone}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Est. Completion</p>
              <p className="text-sm font-medium">{learningPath.estimated_completion_days} days</p>
            </div>
          </CardContent>
        </Card>
      ) : null}

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
          <TabsTrigger value="path" className="flex items-center gap-2">
            <Trophy className="h-4 w-4" />
            Learning Path
          </TabsTrigger>
        </TabsList>

        <TabsContent value="courses" className="space-y-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative min-w-64 flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search courses…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex gap-2">
              {['all', 'beginner', 'intermediate', 'advanced'].map((d) => (
                <Button
                  key={d}
                  variant={selectedDifficulty === d ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedDifficulty(d)}
                >
                  {d.charAt(0).toUpperCase() + d.slice(1)}
                </Button>
              ))}
            </div>
          </div>

          {contentLoading ? (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-52 w-full" />
              ))}
            </div>
          ) : filteredContent.length === 0 ? (
            <div className="py-16 text-center text-sm text-muted-foreground">
              No courses available yet.
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredContent.map((course, i) => (
                <motion.div
                  key={course.id ?? course.content_id ?? i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className="group h-full border-border/50 bg-card/50 transition-all hover:border-accent/50">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-accent/10">
                          <PlayCircle className="h-6 w-6 text-accent" />
                        </div>
                        <Badge
                          variant={
                            (course.difficulty || '').toLowerCase() === 'beginner'
                              ? 'default'
                              : (course.difficulty || '').toLowerCase() === 'intermediate'
                                ? 'secondary'
                                : 'outline'
                          }
                        >
                          {course.difficulty}
                        </Badge>
                      </div>
                      <CardTitle className="mt-4 text-lg">{course.title}</CardTitle>
                      {course.description && (
                        <CardDescription>{course.description}</CardDescription>
                      )}
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-3 text-sm text-muted-foreground">
                        {course.estimated_duration_minutes && (
                          <span className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {course.estimated_duration_minutes} min
                          </span>
                        )}
                        {(course.topic || (course.topics && course.topics[0])) && (
                          <Badge variant="outline" className="text-xs">
                            {course.topic || course.topics![0]}
                          </Badge>
                        )}
                      </div>
                      <Button className="mt-4 w-full gap-1">
                        <PlayCircle className="h-4 w-4" />
                        Start Learning
                        <ChevronRight className="h-3 w-3" />
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="glossary" className="space-y-4">
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search terms…"
              value={glossarySearch}
              onChange={(e) => setGlossarySearch(e.target.value)}
              className="pl-9"
            />
          </div>

          {glossaryLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : !glossaryTerms || glossaryTerms.length === 0 ? (
            <div className="py-16 text-center text-sm text-muted-foreground">
              No glossary terms found.
            </div>
          ) : (
            <Card className="border-border/50 bg-card/50 backdrop-blur">
              <CardContent className="p-4">
                <div className="space-y-4">
                  {glossaryTerms.map((item, i) => (
                    <motion.div
                      key={item.term}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.03 }}
                      className="rounded-lg border border-border/50 bg-background/50 p-4"
                    >
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-accent">{item.term}</h4>
                        {item.category && (
                          <Badge variant="outline" className="text-xs">
                            {item.category}
                          </Badge>
                        )}
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {item.definition}
                      </p>
                      {item.related_terms?.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {item.related_terms.map((t) => (
                            <Badge key={t} variant="secondary" className="text-xs">
                              {t}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="path" className="space-y-4">
          {pathLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : !learningPath || learningPath.learning_path.length === 0 ? (
            <div className="py-16 text-center text-sm text-muted-foreground">
              No learning path available yet.
            </div>
          ) : (
            <Card className="border-border/50 bg-card/50 backdrop-blur">
              <CardHeader>
                <CardTitle>Your Learning Path</CardTitle>
                <CardDescription>
                  Level: <span className="capitalize font-medium">{learningPath.current_level}</span>
                  {' · '}
                  Total: {Math.round(learningPath.total_duration_minutes / 60)} hours
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {learningPath.learning_path.map((step, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.07 }}
                      className="flex items-start gap-4 rounded-lg border border-border/50 bg-background/50 p-4"
                    >
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent/20 text-sm font-bold text-accent">
                        {i + 1}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold">{step.module}</h4>
                          <span className="text-xs text-muted-foreground">
                            {step.duration_minutes} min
                          </span>
                        </div>
                        {step.topics?.length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {step.topics.map((t) => (
                              <Badge key={t} variant="outline" className="text-xs">
                                {t}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
