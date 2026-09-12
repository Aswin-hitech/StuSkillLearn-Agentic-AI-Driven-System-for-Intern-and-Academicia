import { Navigate, Route, Routes } from 'react-router-dom';

import { ProtectedRoute } from './components/ProtectedRoute';
import { PortalShell } from './layouts/PortalShell';
import { AcademicianCurriculumPage, AcademicianDashboardPage, AcademicianOpportunitiesPage } from './pages/AcademicianPages';
import { AgentsPage } from './pages/AgentsPage';
import { LoginPage, RegisterPage } from './pages/AuthPages';
import { CompanyAllocationsPage, CompanyDashboardPage, CompanyLearningPage, CompanyOpportunitiesPage, CompanyRankingsPage } from './pages/CompanyPages';
import { InstitutionAcademicianOpportunitiesPage, InstitutionCurriculumPage, InstitutionDashboardPage, InstitutionReadinessPage } from './pages/InstitutionPages';
import { LandingPage } from './pages/LandingPage';
import { StudentDashboardPage, StudentLearningPage, StudentLSRWPage, StudentOffersPage, StudentOpportunitiesPage, StudentPortfolioPage, StudentPreferencesPage, StudentProfilePage, StudentSkillGapPage } from './pages/StudentPages';

export default function App(){
  return <Routes>
    <Route path="/" element={<LandingPage/>}/>
    <Route path="/login" element={<LoginPage/>}/>
    <Route path="/register/:role" element={<RegisterPage/>}/>

    <Route element={<ProtectedRoute/>}>
      <Route element={<PortalShell/>}>
        <Route element={<ProtectedRoute roles={['STUDENT']}/>}>
          <Route path="/student" element={<StudentDashboardPage/>}/>
          <Route path="/student/profile" element={<StudentProfilePage/>}/>
          <Route path="/student/preferences" element={<StudentPreferencesPage/>}/>
          <Route path="/student/skill-gap" element={<StudentSkillGapPage/>}/>
          <Route path="/student/lsrw" element={<StudentLSRWPage/>}/>
          <Route path="/student/learning" element={<StudentLearningPage/>}/>
          <Route path="/student/portfolio" element={<StudentPortfolioPage/>}/>
          <Route path="/student/opportunities" element={<StudentOpportunitiesPage/>}/>
          <Route path="/student/offers" element={<StudentOffersPage/>}/>
        </Route>
        <Route element={<ProtectedRoute roles={['COMPANY']}/>}>
          <Route path="/company" element={<CompanyDashboardPage/>}/>
          <Route path="/company/opportunities" element={<CompanyOpportunitiesPage/>}/>
          <Route path="/company/rankings" element={<CompanyRankingsPage/>}/>
          <Route path="/company/allocations" element={<CompanyAllocationsPage/>}/>
          <Route path="/company/learning" element={<CompanyLearningPage/>}/>
        </Route>
        <Route element={<ProtectedRoute roles={['ACADEMICIAN']}/>}>
          <Route path="/academician" element={<AcademicianDashboardPage/>}/>
          <Route path="/academician/opportunities" element={<AcademicianOpportunitiesPage/>}/>
          <Route path="/academician/curriculum" element={<AcademicianCurriculumPage/>}/>
        </Route>
        <Route element={<ProtectedRoute roles={['INSTITUTION']}/>}>
          <Route path="/institution" element={<InstitutionDashboardPage/>}/>
          <Route path="/institution/readiness" element={<InstitutionReadinessPage/>}/>
          <Route path="/institution/curriculum" element={<InstitutionCurriculumPage/>}/>
          <Route path="/institution/academician-opportunities" element={<InstitutionAcademicianOpportunitiesPage/>}/>
        </Route>
        <Route path="/agents" element={<AgentsPage/>}/>
      </Route>
    </Route>
    <Route path="*" element={<Navigate to="/" replace/>}/>
  </Routes>;
}
